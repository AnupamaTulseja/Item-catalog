from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from sqlalchemy_utils import database_exists, drop_database, create_database

from database_setup import Category, CategoryItem, Base

engine = create_engine('sqlite:///itemcatalog.db')

Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)

Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)

session = DBSession()



# Items for Italian
category1 = Category(name="Italian")

session.add(category1)
session.commit()

item1 = CategoryItem(name="Bresaola", description="Air-dried, salted beef (but also horse, venison and pork) that has been aged two or three months until it becomes hard and turns a dark red, almost purple colour.", category=category1)

session.add(item1)
session.commit()

item2 = CategoryItem(name="Calzone", description="folded over dough usually filled with ricotta and other ingredients", category=category1)

session.add(item2)
session.commit()


# Items for Thai
category2 = Category(name="Thai")

session.add(category2)
session.commit()

item1 = CategoryItem(name="Khao Kan Chin", description="A dish of the Tai Yai (Shan people) of Myanmar and northern Thailand, it is rice that is mixed with pork blood and steamed inside a banana leaf. Khao kan chin is served with cucumber, onions and fried, dried chillies.", category=category2)

session.add(item1)
session.commit()

item2 = CategoryItem(name="Drunken Noodles", description="Spicy fried wide rice noodles", category=category2)

session.add(item2)
session.commit()

# Items for Chinese
category3 = Category(name="Chinese")

session.add(category3)
session.commit()

item1 = CategoryItem(name="Zongzi", description="glutinous rice wrapped in bamboo leaves, usually with a savory or sweet filling", category=category3)

session.add(item1)
session.commit()

item2 = CategoryItem(name="Century egg", description="A famous snack in parts of China", category=category3)

session.add(item2)
session.commit()

categories = session.query(Category).all()
for category in categories:
    print "Category: " + category.name