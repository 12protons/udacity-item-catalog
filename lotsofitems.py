from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Base, Category, Item

engine = create_engine('sqlite:///itemcatalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Menu for Party Games
category1 = Category(name="Party Games")

session.add(category1)
session.commit()

item1 = Item(name="Codenames", description="Team based word game",
             category=category1)

session.add(item1)
session.commit()

item2 = Item(name="Concept", description="Pictures game", category=category1)

session.add(item2)
session.commit()

item3 = Item(name="Ca$h n Guns", description="Press your luck shootem up",
             category=category1)

session.add(item3)
session.commit()


# Menu for Strategy Games
category2 = Category(name="Strategy Games")

session.add(category2)
session.commit()


item1 = Item(name="Agricola", description="Farming!", category=category2)

session.add(item1)
session.commit()

item2 = Item(name="Caverna", description="Farming and caves!",
             category=category2)

session.add(item2)
session.commit()

item3 = Item(name="Diplomacy", description="Ruins friendships.",
             category=category2)

session.add(item3)
session.commit()


print "added items!"
