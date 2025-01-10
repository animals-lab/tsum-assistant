from sqlmodel import SQLModel
from tsa.config import settings
from tsa.models.catalog import Brand
from tsa.models.customer import Customer, CustomerBrandPreference, CustomerGender, PreferenceType
import asyncio

async def create_tables():
    async with settings.db.engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def seed():
    async with settings.db.async_session_maker() as session:
        # Create Viktor
        viktor = Customer(
            id=1,
            name="Виктор Иванович",
            gender=CustomerGender.MALE,
            age=40,
            style_preferences="Милитари, повседневный стиль, околофутбольные бренды типа StoneIsland и CP company, помимо этого точечно носит вещи ближе к фешен сегменту, типа Maison Margiela. Сникерхед, не носит серийные кроссовки. Иногда носит классику.",
            description="Водит BMW, любит путешествовать, рестораны, играет в Хоккей и катается на сноуборде. Разговоры по делу, не любит спам, знает что хочет. Ценит время и не терпит тупых людей."
        )
        session.add(viktor)
        await session.flush()  # Flush to get the ID

        # Viktor's liked brands
        viktor_liked_brands = ["Stone Island", "Ten C", "C.P. Company", "MM6", "A-COLD-WALL", "A.P.C.", "Acne Studios", "Aspesi"]
        for brand_name in viktor_liked_brands:
            pref = CustomerBrandPreference(
                customer_id=viktor.id,
                brand_name=brand_name,
                preference=PreferenceType.LIKE
            )
            session.add(pref)

        # Viktor's disliked brands
        viktor_disliked_brands = ["Dsquared2", "Dolce & Gabbana", "Diesel", "BOSS", "Emporio Armani", "EA7"]
        for brand_name in viktor_disliked_brands:
            pref = CustomerBrandPreference(
                customer_id=viktor.id,
                brand_name=brand_name,
                preference=PreferenceType.DISLIKE
            )
            session.add(pref)

        # Create Lenochka
        lenochka = Customer(
            id=2,
            name="Леночка",
            gender=CustomerGender.FEMALE,
            age=27,
            style_preferences="Нравится лаконичное, неброское, минималистичное, но с изюминкой - интересная фактура или посадка. Не любит кричащие вещи и самые популярные бренды. В цветах сдержанная палитра, в основном черные, серые, белые вещи, изредка цветные акценты. Не любит синтетику, предпочитает натуральные ткани. Любит удобные вещи. редко носит классику и строгую одежду. Важен комфорт. Позволяла бы себе более яркие образы и экстравагантные вещи при наличии большего бюджета. Любит сочетание дорогих интересных вещей с неброскими простыми вещами.",
            description="замужем, домохозяйка, любит путешествовать, рестораны, светскую жизнь, фестивали, электронную музыку, диско.  эгоцентричная особа, которой нравится внимание. Не будет терпеть косяков и плохой сервис."
        )
        session.add(lenochka)
        await session.flush()  # Flush to get the ID

        # Lenochka's liked brands
        lenochka_liked_brands = ["The New Arrivals Ilkyaz Ozel", "Yuzefi", "Acne Studios", "Andrea Ya'aqov", "MM6", "Juun.J", "Ganni"]
        for brand_name in lenochka_liked_brands:
            pref = CustomerBrandPreference(
                customer_id=lenochka.id,
                brand_name=brand_name,
                preference=PreferenceType.LIKE
            )
            session.add(pref)

        # Lenochka's disliked brands
        lenochka_disliked_brands = ["Off-White", "Palm Angels", "JW Anderson"]
        for brand_name in lenochka_disliked_brands:
            pref = CustomerBrandPreference(
                customer_id=lenochka.id,
                brand_name=brand_name,
                preference=PreferenceType.DISLIKE
            )
            session.add(pref)

        await session.commit()


if __name__ == "__main__":
    asyncio.run(create_tables())
    asyncio.run(seed())
