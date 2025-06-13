from backend.models.card import CardORM, Card
from sqlalchemy.orm import Session
from typing import List

def get_cards(db: Session) -> List[Card]:
    return [Card.model_validate(card) for card in db.query(CardORM).order_by(CardORM.created_at.desc()).all()]

def get_card(db: Session, card_id: int) -> Card:
    card = db.query(CardORM).filter(CardORM.id == card_id).first()
    return Card.model_validate(card) if card else None

def create_card(db: Session, card: Card) -> Card:
    db_card = CardORM(**card.model_dump(exclude_unset=True))
    db.add(db_card)
    db.commit()
    db.refresh(db_card)
    return Card.model_validate(db_card)

def update_card(db: Session, card_id: int, card: Card) -> Card:
    db_card = db.query(CardORM).filter(CardORM.id == card_id).first()
    if not db_card:
        return None
    
    # 獲取要更新的數據，排除 None 值和 id 字段
    update_data = card.model_dump(exclude_unset=True, exclude={'id'})
    
    for k, v in update_data.items():
        if hasattr(db_card, k):
            setattr(db_card, k, v)
    
    try:
        db.commit()
        db.refresh(db_card)
        return Card.model_validate(db_card)
    except Exception as e:
        db.rollback()
        print(f"更新名片錯誤: {e}")
        raise e

def delete_card(db: Session, card_id: int) -> bool:
    db_card = db.query(CardORM).filter(CardORM.id == card_id).first()
    if not db_card:
        return False
    try:
        db.delete(db_card)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"刪除名片錯誤: {e}")
        return False 