import { OpenAI } from 'openai';
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();
const openai = new OpenAI({
  apiKey: process.env.AI_API_KEY,
  baseURL: process.env.AI_BASE_URL
});

export const generateSmartRoute = async (userId, query, budget, daysCount) => {
  try {
    const availablePlaces = await prisma.place.findMany({
      where: { avgCost: { lte: budget } },
      select: { name: true, region: true, description: true, avgCost: true }
    });

    const systemPrompt = `Ты — интеллектуальный цифровой гид по Казахстану "Uly Dala".
Твоя задача — составить оптимальный travel-маршрут по дням на основе реальных мест.
Используй ТОЛЬКО данные из этого списка проверенных локаций: ${JSON.stringify(availablePlaces)}.
Категорически запрещено выдумывать несуществующие цены или отели. Отвечай СТРОГО в формате JSON.
Если бюджет слишком мал или мест не найдено, верни объект с полем "error".`;

    const completion = await openai.chat.completions.create({
      model: process.env.AI_MODEL_NAME,
      messages: [
        { role: "system", content: systemPrompt },
        { role: "user", content: `Запрос: "${query}". Бюджет: ${budget} тенге. Количество дней: ${daysCount}.` }
      ],
      response_format: { type: "json_object" },
      temperature: 0.2
    });

    const routeData = JSON.parse(completion.choices[0].message.content);

    if (routeData.error) {
      return { success: false, message: routeData.error };
    }

    const savedTrip = await prisma.trip.create({
      data: { userId, query, budget, daysCount, routeJson: routeData }
    });

    return { success: true, data: savedTrip };
  } catch (error) {
    console.error("AI Service Error:", error);
    return { success: false, message: "Внутренняя ошибка генерации маршрута ИИ" };
  }
};
