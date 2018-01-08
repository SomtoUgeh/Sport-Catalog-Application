from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Base, User, Sport, SportItem

engine = create_engine('sqlite:///sportcategory.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()

# Creating a dummy User
User1 = User(name="Admin", email="admin@catalog.com",
             image='https://cdn-images-1.medium.com/max/1200/1*8I9Bsu69nfnzYERIeHQo3Q@2x.jpeg')
session.add(User1)
session.commit()

# Creating a sport category
Sport1 = Sport(user_id=1, name="Soccer")
session.add(Sport1)
session.commit()

Sport2 = Sport(user_id=1, name="Basketball")
session.add(Sport2)
session.commit()

Sport3 = Sport(user_id=1, name="Hockey")
session.add(Sport3)
session.commit()

Sport4 = Sport(user_id=1, name="Swimming")
session.add(Sport4)
session.commit()

Sport5 = Sport(user_id=1, name="Boxing")
session.add(Sport5)
session.commit()

Sport6 = Sport(user_id=1, name="Wrestling")
session.add(Sport6)
session.commit()

Sport7 = Sport(user_id=1, name="Tennis")
session.add(Sport7)
session.commit()

Sport8 = Sport(user_id=1, name="Tracks")
session.add(Sport8)
session.commit()

Sport9 = Sport(user_id=1, name="High Jump")
session.add(Sport9)
session.commit()

# Creating a new sport category item
SportItem1 = SportItem(user_id=1, name="Soccer ball", description='A football, soccer ball, or association football '
                                                                  'ball is the ball used in the sport of association '
                                                                  'football. The name of the ball varies according to '
                                                                  'whether the sport is called "football", "soccer", '
                                                                  'or "association football". The ball"s spherical '
                                                                  'shape, as well as its size, weight, and material '
                                                                  'composition, are specified by Law 2 of the Laws of '
                                                                  'the Game maintained by the International Football '
                                                                  'Association Board. Additional, more stringent, '
                                                                  'standards are specified by FIFA and subordinate '
                                                                  'governing bodies for the balls used in the '
                                                                  'competitions they sanction.', sport_id=1)
session.add(SportItem1)
session.commit()

SportItem2 = SportItem(user_id=1, name="Football Jersey", description='A garment worn by soccer players during a'
                                                                      'game. It can be sold to make profit for the team,'
                                                                      'also as a show of commitment for the fans',
                       sport_id=1)
session.add(SportItem2)
session.commit()

SportItem3 = SportItem(user_id=1, name="Basketball Jersey", description='A garment worn by basket ball players during a'
                                                                        'game. It can be sold to make profit for the team,'
                                                                        'also as a show of commitment for the fans',
                       sport_id=2)
session.add(SportItem3)
session.commit()

SportItem4 = SportItem(user_id=1, name="Basketball ball", description='A ball used by the basketball players for a '
                                                                      'game, it is usually sort after by teams during'
                                                                      'the game.', sport_id=2)
session.add(SportItem4)
session.commit()

SportItem5 = SportItem(user_id=1, name="Hockey Stick",
                       description='An L-shaped stick used by hockey players during the games.'
                                   'it is used to play the ball around', sport_id=3)
session.add(SportItem5)
session.commit()

SportItem6 = SportItem(user_id=1, name="Hockey Jersey",
                       description='A garment usually worn the hockey players during the game.'
                                   'it can also be for profit for the teammmm.', sport_id=6)
session.add(SportItem6)
session.commit()

SportItem7 = SportItem(user_id=1, name="Swimming trunk",
                       description='A garment usually worn the swimmers during the race.'
                       , sport_id=4)
session.add(SportItem7)
session.commit()

SportItem8 = SportItem(user_id=1, name="Hockey Jersey",
                       description='A garment usually worn the hockey players during the game.'
                                   'it can also be for profit for the teammmm.', sport_id=6)
session.add(SportItem8)
session.commit()
