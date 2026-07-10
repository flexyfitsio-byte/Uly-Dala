import express from 'express';
import bcrypt from 'bcryptjs';
import jwt from 'jsonwebtoken';
import { PrismaClient } from '@prisma/client';

const router = express.Router();
const prisma = new PrismaClient();

router.post('/register', async (req, res) => {
  const { email, password, fullName } = req.body;

  if (!email || !password || !fullName) {
    return res.status(400).json({ error: "Заполните все поля: email, password, fullName" });
  }

  try {
    const existing = await prisma.user.findUnique({ where: { email } });
    if (existing) {
      return res.status(409).json({ error: "Пользователь с таким email уже существует" });
    }

    const passwordHash = await bcrypt.hash(password, 10);

    const user = await prisma.user.create({
      data: { email, passwordHash, fullName }
    });

    const token = jwt.sign(
      { id: user.id, email: user.email },
      process.env.JWT_SECRET,
      { expiresIn: '7d' }
    );

    return res.status(201).json({
      token,
      user: { id: user.id, email: user.email, fullName: user.fullName, xp: user.xp, level: user.level }
    });
  } catch (error) {
    console.error("Register error:", error);
    return res.status(500).json({ error: "Ошибка регистрации" });
  }
});

router.post('/login', async (req, res) => {
  const { email, password } = req.body;

  if (!email || !password) {
    return res.status(400).json({ error: "Заполните все поля: email, password" });
  }

  try {
    const user = await prisma.user.findUnique({ where: { email } });
    if (!user) {
      return res.status(401).json({ error: "Неверный email или пароль" });
    }

    const validPassword = await bcrypt.compare(password, user.passwordHash);
    if (!validPassword) {
      return res.status(401).json({ error: "Неверный email или пароль" });
    }

    const token = jwt.sign(
      { id: user.id, email: user.email },
      process.env.JWT_SECRET,
      { expiresIn: '7d' }
    );

    return res.status(200).json({
      token,
      user: { id: user.id, email: user.email, fullName: user.fullName, xp: user.xp, level: user.level }
    });
  } catch (error) {
    console.error("Login error:", error);
    return res.status(500).json({ error: "Ошибка входа" });
  }
});

router.get('/me', async (req, res) => {
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.split(' ')[1];
  if (!token) return res.status(401).json({ error: "Токен отсутствует" });

  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    const user = await prisma.user.findUnique({
      where: { id: decoded.id },
      select: { id: true, email: true, fullName: true, xp: true, level: true, createdAt: true }
    });
    if (!user) return res.status(404).json({ error: "Пользователь не найден" });
    return res.status(200).json(user);
  } catch {
    return res.status(403).json({ error: "Невалидный токен" });
  }
});

export default router;
