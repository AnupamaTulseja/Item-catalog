import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

class Category(Base):
    __tablename__ = 'category'

    id = Column(Integer, primary_key = True)
    name = Column(String(80), nullable = False)


    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id': self.id,
            'name': self.name,
        }

class CategoryItem(Base):
    __tablename__ = 'category_item'

    name = Column(String(80), nullable = False)
    description = Column(String(250))
    id = Column(Integer, primary_key = True)
    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship(Category)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'category': self.category.name,
            'description': self.description,
            'name': self.name,
        }

engine = create_engine('sqlite:///itemcatalog.db')
Base.metadata.create_all(engine)