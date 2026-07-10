import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

const places = [
  {
    name: "Боровое (Бурабай)",
    region: "Акмолинская область",
    description: "Национальный парк с горными озёрами, соснами и скалами, популярное направление на выходные.",
    history: "Курортная зона, известная с XIX века как 'казахстанская Швейцария'.",
    latitude: 53.0850,
    longitude: 70.3097,
    avgCost: 60000,
    category: "Природа"
  },
  {
    name: "Мавзолей Ходжи Ахмеда Ясави",
    region: "Туркестан",
    description: "Памятник ЮНЕСКО, построенный по приказу Тамерлана в XIV веке.",
    history: "Один из главных объектов духовного паломничества тюркского мира.",
    latitude: 43.2975,
    longitude: 68.2517,
    avgCost: 45000,
    category: "История"
  },
  {
    name: "Чарынский каньон",
    region: "Алматинская область",
    description: "Каньон, напоминающий Гранд-Каньон, с уникальными скальными формациями.",
    history: "Формировался миллионы лет под воздействием реки Чарын и ветровой эрозии.",
    latitude: 43.3500,
    longitude: 79.0667,
    avgCost: 35000,
    category: "Природа"
  },
  {
    name: "Кольсайские озёра",
    region: "Алматинская область",
    description: "Три горных озера, известные как 'жемчужины Северного Тянь-Шаня'.",
    history: "Одно из самых живописных мест Заилийского Алатау, популярно для треккинга.",
    latitude: 42.9333,
    longitude: 78.4167,
    avgCost: 40000,
    category: "Природа"
  },
  {
    name: "Медеу и Шымбулак",
    region: "Алматы",
    description: "Высокогорный каток и горнолыжный курорт над Алматы.",
    history: "Медеу — один из самых высокогорных катков в мире, действует с 1949 года.",
    latitude: 43.1547,
    longitude: 77.0592,
    avgCost: 25000,
    category: "Активный отдых"
  }
];

async function main() {
  console.log('Заполняем базу тестовыми местами...');

  for (const place of places) {
    await prisma.place.upsert({
      where: { name: place.name },
      update: {},
      create: place
    });
  }

  console.log(`Готово: добавлено/проверено ${places.length} мест.`);
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
