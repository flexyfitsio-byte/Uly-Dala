import express from 'express';
import { PrismaClient } from '@prisma/client';
import { authenticateToken } from '../middleware/auth.js';

const router = express.Router();
const prisma = new PrismaClient();

router.post('/passport/stamp', authenticateToken, async (req, res) => {
  const { placeName } = req.body;
  const userId = req.user.id;

  try {
    const existingStamp = await prisma.passportStamp.findFirst({
      where: { userId, placeName }
    });

    if (existingStamp) {
      return res.status(400).json({ message: "Штамп в Uly Passport уже получен" });
    }

    const stamp = await prisma.passportStamp.create({
      data: { userId, placeName }
    });

    const updatedUser = await prisma.user.update({
      where: { id: userId },
      data: { xp: { increment: 200 } }
    });

    let newLevel = updatedUser.level;
    if (updatedUser.xp > 5000) newLevel = "Легенда Великой степи";
    else if (updatedUser.xp > 2000) newLevel = "Знаток Казахстана";
    else if (updatedUser.xp > 1000) newLevel = "Исследователь";
    else if (updatedUser.xp > 300) newLevel = "Путешественник";

    if (newLevel !== updatedUser.level) {
      await prisma.user.update({
        where: { id: userId },
        data: { level: newLevel }
      });
    }

    return res.status(201).json({ success: true, stamp, xp: updatedUser.xp, level: newLevel });
  } catch (error) {
    return res.status(500).json({ error: error.message });
  }
});

// Список полученных штампов пользователя
router.get('/passport/stamps', authenticateToken, async (req, res) => {
  try {
    const stamps = await prisma.passportStamp.findMany({
      where: { userId: req.user.id },
      orderBy: { visitedAt: 'desc' }
    });
    return res.status(200).json(stamps);
  } catch (error) {
    return res.status(500).json({ error: error.message });
  }
});

// Список сохранённых маршрутов пользователя
router.get('/trips', authenticateToken, async (req, res) => {
  try {
    const trips = await prisma.trip.findMany({
      where: { userId: req.user.id },
      orderBy: { createdAt: 'desc' }
    });
    return res.status(200).json(trips);
  } catch (error) {
    return res.status(500).json({ error: error.message });
  }
});

export default router;
