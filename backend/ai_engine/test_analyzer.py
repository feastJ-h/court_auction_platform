from backend.ai_engine.analyzer import is_hallucinated, normalize_payload


def test_payload_validation() -> None:
    payload = normalize_payload(
        {
            "main_category": "부동산",
            "sub_category": "아파트",
            "address": "서울특별시 강남구",
            "item_details": "전용면적 84제곱미터 아파트. 12층 중 5층.",
            "min_price": "100,000,000원",
            "bidding_date": "2026년 7월 20일",
            "risk_comment": "등기부 확인 필요",
        }
    )
    assert payload["main_category"] == "부동산"
    assert payload["min_price"] == "100000000"
    assert payload["bidding_date"] == "2026-07-20"
    assert payload["analysis_provider"] == "chatgpt"
    assert not is_hallucinated(payload)
    assert is_hallucinated({"address": "서울"})


if __name__ == "__main__":
    test_payload_validation()
    print("Sprint 5 AI analyzer unit test passed")
