import express from 'express';
import { generateSmartRoute } from '../services/aiService.js';
import { authenticateToken } from '../middleware/auth.js';

const router = express.Router();

router.post('/generate-route', authenticateToken, async (req, res) => {
  const { query, budget, daysCount } = req.body;
  const userId = req.user.id;

  if (!query || !budget || !daysCount) {
    return res.status(400).json({ error: "Заполните все поля: query, budget, daysCount" });
  }

  const result = await generateSmartRoute(userId, query, parseInt(budget), parseInt(daysCount));

  if (!result.success) {
    return res.status(422).json({ error: result.message });
  }

  return res.status(200).json(result.data);
});

export default router;
