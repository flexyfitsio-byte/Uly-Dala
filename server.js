import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import authRoutes from './routes/authRoutes.js';
import aiRoutes from './routes/aiRoutes.js';
import gameRoutes from './routes/gameRoutes.js';

dotenv.config();

const app = express();
const PORT = process.env.PORT || 5000;

app.use(cors());
app.use(express.json());

app.get('/', (req, res) => {
  res.status(200).json({ project: "Uly Dala API", status: "running" });
});

// Роут проверки жизнеспособности сервера
app.get('/health', (req, res) => {
  res.status(200).json({ status: "alive", project: "Uly Dala API" });
});

// Подключение маршрутов
app.use('/api/auth', authRoutes);
app.use('/api/ai', aiRoutes);
app.use('/api/game', gameRoutes);

app.listen(PORT, () => {
  console.log(`Сервер запущен на порту ${PORT}`);
});
