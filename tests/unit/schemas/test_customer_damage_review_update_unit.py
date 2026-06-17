from app.schemas.customer import DamageReviewUpdate


def test_damage_review_update_defaults_new_status() -> None:
    model = DamageReviewUpdate()
    assert model.new_status == "Claims Reviewed"


def test_damage_review_update_accepts_full_payload() -> None:
    model = DamageReviewUpdate(
        damage_severity="MEDIUM",
        is_genuine=True,
        recommended_settlement="Partial Refund",
        remarks="Validated by warehouse team",
        new_status="Approved",
    )

    assert model.damage_severity == "MEDIUM"
    assert model.is_genuine is True
    assert model.new_status == "Approved"
