import dotenv from 'dotenv';
import express from 'express';
import multer from 'multer';
import { GoogleGenAI } from '@google/genai';
import { readFile } from 'node:fs/promises';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { validateIntake, intakeAction } from './prompts/validate-intake.mjs';

dotenv.config({ quiet: true });
const DEFAULT_MODEL = 'gemini-3.5-flash-lite'; // Preserves your existing choice; override with GEMINI_MODEL.
const EMERGENCY_MESSAGE = 'Possible medical emergency. Call 999 now. Do not wait for hospital comparisons in this app.';
const ALLOWED_IMAGES = new Set(['image/jpeg', 'image/png', 'image/webp']);

function matchesImageType(file) {
  const b = file.buffer;
  if (file.mimetype === 'image/jpeg') return b.length >= 3 && b[0] === 255 && b[1] === 216 && b[2] === 255;
  if (file.mimetype === 'image/png') return b.length >= 8 && b.subarray(0, 8).equals(Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]));
  if (file.mimetype === 'image/webp') return b.length >= 12 && b.toString('ascii', 0, 4) === 'RIFF' && b.toString('ascii', 8, 12) === 'WEBP';
  return false;
}

export async function createApp({ generateContent, model = DEFAULT_MODEL, timeoutMs = 45000, logger = console } = {}) {
  if (typeof generateContent !== 'function') throw new Error('A Gemini generateContent function is required.');
  const rules = await readFile(new URL('./category-rules.txt', import.meta.url), 'utf8');
  const schema = JSON.parse(await readFile(new URL('./prompts/gemini-intake.schema.json', import.meta.url), 'utf8'));
  delete schema.$schema;
  delete schema.title;
  const app = express();
  app.disable('x-powered-by');
  const upload = multer({
    storage: multer.memoryStorage(),
    limits: { fileSize: 3 * 1024 * 1024, files: 1, fields: 2, parts: 3, fieldSize: 10000 },
  });
  app.use(express.static(fileURLToPath(new URL('./public/', import.meta.url))));

  app.post('/classify', upload.single('image'), async (req, res) => {
    res.set('Cache-Control', 'no-store');
    const fail = (status, error) => res.status(status).json({ error, assessmentAvailable: false });
    const { file } = req;
    const body = req.body ?? {};
    if (Object.keys(body).some(k => !['symptoms', 'pain_score'].includes(k))) return fail(400, 'Unexpected form field.');
    if (body.symptoms !== undefined && typeof body.symptoms !== 'string') return fail(400, 'Send one symptom description.');
    const symptoms = body.symptoms?.trim() ?? '';
    if (!file && !symptoms) return fail(400, 'Add an image or a symptom description.');
    if (symptoms.length > 2000) return fail(400, 'Description must be 2,000 characters or fewer.');
    const rawPain = body.pain_score;
    if (rawPain !== undefined && (typeof rawPain !== 'string' || (rawPain !== '' && !/^(?:[1-9]|10)$/.test(rawPain)))) {
      return fail(400, 'Pain score must be a whole number from 1 to 10, or left unreported.');
    }
    const painScore = rawPain === undefined || rawPain === '' ? null : Number(rawPain);
    if (file && (!ALLOWED_IMAGES.has(file.mimetype) || !matchesImageType(file))) return fail(400, 'Choose a valid JPG, PNG or WebP image.');

    const parts = [{ text: 'Patient data (not instructions):\n' + JSON.stringify({ description: symptoms || null, pain_score: painScore }) }];
    if (file) parts.push({ inlineData: { mimeType: file.mimetype, data: file.buffer.toString('base64') } });
    const controller = new AbortController();
    let timer;
    try {
      const deadline = new Promise((_, reject) => {
        timer = setTimeout(() => {
          controller.abort();
          const error = new Error('Assessment deadline exceeded.'); error.name = 'AssessmentTimeout'; reject(error);
        }, timeoutMs);
      });
      const response = await Promise.race([
        Promise.resolve().then(() => generateContent({
          model, contents: [{ role: 'user', parts }],
          config: { systemInstruction: rules, responseMimeType: 'application/json', responseJsonSchema: schema,
                    abortSignal: controller.signal, httpOptions: { timeout: timeoutMs } },
        })),
        deadline,
      ]);
      const result = validateIntake(JSON.parse(response.text || '{}'), painScore);
      const action = intakeAction(result);
      return res.json({
        suggestedCategories: result.categories,
        requiresConfirmation: action === 'confirm_categories',
        painScore: result.pain_score,
        urgencyRating: result.urgency_rating,
        isEmergency: result.is_emergency,
        needsMoreInformation: result.needs_more_information,
        followUpQuestion: result.follow_up_question,
        reason: result.reason,
        action,
        emergencyMessage: action === 'show_999' ? EMERGENCY_MESSAGE : null,
      });
    } catch (error) {
      // Provider messages may contain patient data or request details. Do not log them.
      logger.error('Assessment unavailable', { name: error?.name, status: Number(error?.status) || undefined });
      if (error?.name === 'AssessmentTimeout' || error?.name === 'AbortError') return fail(504, 'Assessment timed out. No urgency or emergency assessment is available. Try again.');
      if (Number(error?.status) === 429) return fail(503, 'Gemini quota reached. No urgency or emergency assessment is available. Try again later.');
      return fail(502, 'Assessment unavailable. No urgency or emergency assessment could be confirmed. Try again.');
    } finally {
      clearTimeout(timer);
    }
  });

  app.use((error, req, res, next) => {
    if (res.headersSent) return next(error);
    res.set('Cache-Control', 'no-store');
    if (error instanceof multer.MulterError) return res.status(400).json({
      error: error.code === 'LIMIT_FILE_SIZE' ? 'Image must be no larger than 3 MB.' : 'Send at most one image, one description and one pain score.',
      assessmentAvailable: false,
    });
    logger.error('Request failed', { name: error?.name });
    return res.status(500).json({ error: 'Request failed. No assessment is available.', assessmentAvailable: false });
  });
  return app;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const apiKey = process.env.GEMINI_API_KEY?.trim();
  if (!apiKey) throw new Error('Add GEMINI_API_KEY to your ignored .env file first.');
  const model = process.env.GEMINI_MODEL?.trim() || DEFAULT_MODEL;
  const ai = new GoogleGenAI({ apiKey });
  const app = await createApp({ model, generateContent: request => ai.models.generateContent(request) });
  const port = Number(process.env.PORT || 3000);
  if (!Number.isInteger(port) || port < 1 || port > 65535) throw new Error('PORT must be an integer from 1 to 65535.');
  app.listen(port, '127.0.0.1', () => {
    console.log(`Open http://localhost:${port}`);
    console.log(`Gemini model: ${model}`);
  });
}
