from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from backend.config import get_settings


class OnbidClientError(RuntimeError):
    pass


DEFAULT_REAL_ESTATE_LIST_BASE_URL = "https://apis.data.go.kr/B010003/OnbidRlstListSrvc2"
DEFAULT_REAL_ESTATE_LIST_OPERATION = "getRlstCltrList2"
DEFAULT_REAL_ESTATE_DETAIL_BASE_URL = "https://apis.data.go.kr/B010003/OnbidRlstDtlSrvc2"
DEFAULT_REAL_ESTATE_DETAIL_OPERATION = "getRlstDtlInf2"
DEFAULT_MOVABLE_LIST_BASE_URL = "https://apis.data.go.kr/B010003/OnbidMvastListSrvc2"
DEFAULT_MOVABLE_LIST_OPERATION = "getMvastCltrList2"
DEFAULT_MOVABLE_DETAIL_BASE_URL = "https://apis.data.go.kr/B010003/OnbidMvastDtlSrvc2"
DEFAULT_MOVABLE_DETAIL_OPERATION = "getMvastDtlInf2"
DEFAULT_NOTICE_LIST_BASE_URL = "https://apis.data.go.kr/B010003/OnbidPbancListSrvc2"
DEFAULT_NOTICE_LIST_OPERATION = "getPbancList2"
DEFAULT_NOTICE_DETAIL_BASE_URL = "https://apis.data.go.kr/B010003/OnbidPbancDtlnfSrvc2"
DEFAULT_NOTICE_DETAIL_OPERATION = "getPbancDtlInf2"
DEFAULT_NOTICE_CLTR_BASE_URL = "https://apis.data.go.kr/B010003/OnbidPbancCltrDtlSrvc2"
DEFAULT_NOTICE_CLTR_OPERATION = "getPbancCltrInf2"


@dataclass(frozen=True)
class OnbidSyncResult:
    fetched: int
    source: str
    used_sample: bool
    total_count: int = 0


SAMPLE_REAL_ESTATE_ITEMS: list[dict[str, Any]] = [
    {
        "source": "ONBID",
        "cltrMngNo": "ONBID-REAL-202607-001",
        "pbctCdtnNo": "PBCT-001",
        "pbancMngNo": "PBANC-202607-A",
        "itemName": "서울 종로구 숭인동 오피스텔 공매",
        "assetType": "부동산",
        "disposalMethod": "매각",
        "bidMethod": "전자입찰",
        "address": "서울 종로구 숭인동 1368",
        "appraisalPrice": 320000000,
        "minimumBidPrice": 250000000,
        "bidDeposit": 25000000,
        "bidStartAt": "2026-08-06",
        "bidEndAt": "2026-08-13",
        "openBidAt": "2026-08-14",
        "status": "입찰예정",
        "agencyName": "한국자산관리공사",
        "landArea": "대지권 8.2㎡",
        "buildingArea": "전용 28.4㎡",
        "landCategory": "대",
        "usage": "업무시설/오피스텔",
        "itemDescription": "회생·파산 자산 검토용 샘플 공매 물건입니다.",
        "bidCondition": "입찰보증금은 최저입찰가의 10% 기준입니다.",
        "contractCondition": "낙찰 후 지정 기한 내 계약 및 잔금 납부 필요",
        "cautions": "현황 및 권리관계는 공고문과 등기부를 별도 확인해야 합니다.",
        "attachmentSummary": "공고문 PDF, 감정평가 요약",
        "noticeTitle": "부동산 공매 공고",
        "noticeBody": "서울 종로구 숭인동 소재 오피스텔 매각 공고 샘플입니다.",
    },
    {
        "source": "ONBID",
        "cltrMngNo": "ONBID-REAL-202607-002",
        "pbctCdtnNo": "PBCT-002",
        "pbancMngNo": "PBANC-202607-B",
        "itemName": "충남 보령시 임야 지분 공매",
        "assetType": "부동산",
        "disposalMethod": "매각",
        "bidMethod": "전자입찰",
        "address": "충남 보령시 천북면 낙동리 산 138-8",
        "appraisalPrice": 12000000,
        "minimumBidPrice": 6000000,
        "bidDeposit": 600000,
        "bidStartAt": "2026-07-12",
        "bidEndAt": "2026-07-17",
        "openBidAt": "2026-07-20",
        "status": "입찰중",
        "agencyName": "한국자산관리공사",
        "landArea": "임야 1,240㎡ 중 지분",
        "landCategory": "임야",
        "usage": "보전관리지역 가능성 검토 필요",
        "itemDescription": "토지 지분과 접근로 확인이 필요한 공매 샘플입니다.",
        "bidCondition": "공유자 우선매수 및 지분권 관계 확인 필요",
        "contractCondition": "잔금 납부 후 소유권 이전",
        "cautions": "지분 물건으로 환가 기간이 길어질 수 있습니다.",
        "attachmentSummary": "공고문 PDF",
        "noticeTitle": "임야 지분 공매 공고",
        "noticeBody": "충남 보령시 임야 지분 매각 공고 샘플입니다.",
    },
    {
        "source": "ONBID",
        "cltrMngNo": "ONBID-REAL-202607-003",
        "pbctCdtnNo": "PBCT-003",
        "pbancMngNo": "PBANC-202607-C",
        "itemName": "인천 계양구 근린생활시설 공매",
        "assetType": "부동산",
        "disposalMethod": "매각",
        "bidMethod": "전자입찰",
        "address": "인천 계양구 작전동",
        "appraisalPrice": 540000000,
        "minimumBidPrice": 378000000,
        "bidDeposit": 37800000,
        "bidStartAt": "2026-07-20",
        "bidEndAt": "2026-07-25",
        "openBidAt": "2026-07-28",
        "status": "유찰",
        "agencyName": "한국자산관리공사",
        "landArea": "대지권 확인 필요",
        "buildingArea": "전용 82.1㎡",
        "landCategory": "대",
        "usage": "근린생활시설",
        "itemDescription": "상가성 부동산 공매 샘플입니다.",
        "bidCondition": "유찰 이력에 따른 가격 추적 필요",
        "contractCondition": "관리비 및 점유관계 확인 필요",
        "cautions": "임차인 및 관리비 체납 여부 확인 필요",
        "attachmentSummary": "공고문 PDF, 사진",
        "noticeTitle": "근린생활시설 공매 공고",
        "noticeBody": "인천 계양구 소재 근린생활시설 매각 공고 샘플입니다.",
    },
]


SAMPLE_REAL_ESTATE_DETAILS: dict[str, dict[str, Any]] = {
    "ONBID-REAL-202607-001": {
        "cltrMngNo": "ONBID-REAL-202607-001",
        "pbctCdtnNo": "PBCT-001",
        "dtlDspsMthodNm": "전자자산처분시스템 입찰",
        "rightAnalysisNote": "등기부, 전입세대, 관리비 체납 여부를 현장 확인해야 합니다.",
        "itemDescription": "상세 API 샘플: 소형 오피스텔, 대중교통 접근성이 있는 물건입니다.",
        "bidCondition": "입찰 전 현황조사서, 감정평가서, 공고문 전체를 확인해야 합니다.",
        "contractCondition": "낙찰 후 계약보증금 납부 및 잔금 일정 준수 필요",
        "cautions": "공부와 현황이 다를 수 있으며 점유관계 인수 가능성을 검토해야 합니다.",
        "attachmentSummary": "상세 공고문, 감정평가 요약, 현황 사진",
    },
    "ONBID-REAL-202607-002": {
        "cltrMngNo": "ONBID-REAL-202607-002",
        "pbctCdtnNo": "PBCT-002",
        "rightAnalysisNote": "공유자 우선매수, 지분 처분 가능성, 진입로를 확인해야 합니다.",
        "itemDescription": "상세 API 샘플: 임야 지분 물건으로 환가 기간을 보수적으로 잡아야 합니다.",
        "cautions": "토지이용계획과 맹지 여부를 별도 검토해야 합니다.",
        "attachmentSummary": "상세 공고문, 토지대장 요약",
    },
    "ONBID-REAL-202607-003": {
        "cltrMngNo": "ONBID-REAL-202607-003",
        "pbctCdtnNo": "PBCT-003",
        "rightAnalysisNote": "상가 임대차, 관리비, 원상복구 비용을 확인해야 합니다.",
        "itemDescription": "상세 API 샘플: 근린생활시설 물건으로 수익성과 공실 리스크를 함께 봅니다.",
        "cautions": "유찰 이력이 있어 보수적 가격 산정이 필요합니다.",
        "attachmentSummary": "상세 공고문, 감정평가 요약, 사진",
    },
}


SAMPLE_MOVABLE_ITEMS: list[dict[str, Any]] = [
    {
        "source": "ONBID",
        "cltrMngNo": "ONBID-MOVABLE-202607-001",
        "pbctCdtnNo": "MPBCT-001",
        "pbancMngNo": "MPBANC-202607-A",
        "onbidCltrno": "M-CLTR-001",
        "pbctNo": "MPBCTNO-001",
        "pbctNsq": "1",
        "itemName": "법인 회생 보유 승합차 공매",
        "assetType": "동산",
        "disposalMethod": "매각",
        "bidMethod": "전자입찰",
        "address": "경기 고양시 일산동구 보관창고",
        "appraisalPrice": 18000000,
        "minimumBidPrice": 12600000,
        "bidDeposit": 1260000,
        "bidStartAt": "2026-08-01",
        "bidEndAt": "2026-08-07",
        "openBidAt": "2026-08-10",
        "status": "입찰예정",
        "agencyName": "한국자산관리공사",
        "usage": "차량",
        "itemDescription": "동산 API 샘플: 연식, 주행거리, 보관장소 확인이 필요한 승합차입니다.",
        "bidCondition": "현장 확인 후 입찰 권장",
        "contractCondition": "낙찰자 직접 이전 및 인수",
        "cautions": "배터리, 사고 이력, 체납 과태료를 확인해야 합니다.",
        "attachmentSummary": "차량 사진, 등록원부 요약",
        "noticeTitle": "동산 공매 공고",
        "noticeBody": "승합차 매각 공고 샘플입니다.",
    },
    {
        "source": "ONBID",
        "cltrMngNo": "ONBID-MOVABLE-202607-002",
        "pbctCdtnNo": "MPBCT-002",
        "pbancMngNo": "MPBANC-202607-B",
        "onbidCltrno": "M-CLTR-002",
        "pbctNo": "MPBCTNO-002",
        "pbctNsq": "1",
        "itemName": "식품 제조라인 기계장치 일괄 공매",
        "assetType": "동산",
        "disposalMethod": "매각",
        "bidMethod": "전자입찰",
        "address": "충북 음성군 공장 내 보관",
        "appraisalPrice": 85000000,
        "minimumBidPrice": 51000000,
        "bidDeposit": 5100000,
        "bidStartAt": "2026-07-25",
        "bidEndAt": "2026-07-31",
        "openBidAt": "2026-08-03",
        "status": "입찰중",
        "agencyName": "한국자산관리공사",
        "usage": "기계장치",
        "itemDescription": "동산 API 샘플: 철거, 운반, 설치 비용을 감안해야 하는 생산설비입니다.",
        "bidCondition": "일괄 매각 조건",
        "contractCondition": "낙찰자 철거 및 반출 책임",
        "cautions": "부품 결품, 작동상태, 전기 인입 조건을 확인해야 합니다.",
        "attachmentSummary": "설비 목록, 현장 사진",
        "noticeTitle": "기계장치 공매 공고",
        "noticeBody": "식품 제조라인 기계장치 일괄 매각 공고 샘플입니다.",
    },
]


SAMPLE_NOTICE_ITEMS: list[dict[str, Any]] = [
    {
        "source": "ONBID",
        "pbancMngNo": "NOTICE-202607-A",
        "noticeNo": "NOTICE-202607-A",
        "pbancNm": "ONBID sample notice for real estate sale",
        "pbancStatNm": "OPEN",
        "pbancKndNm": "SALE",
        "opbdDt": "20260706",
        "opbdDtStart": "202607060900",
        "opbdDtEnd": "202607121800",
        "opengDt": "202607130900",
        "orgNm": "KAMCO",
        "deptNm": "Asset disposal team",
        "dspsMthodNm": "Sale",
        "cptnMthodNm": "Online bid",
        "cltrCnt": "2",
    },
    {
        "source": "ONBID",
        "pbancMngNo": "NOTICE-202607-B",
        "noticeNo": "NOTICE-202607-B",
        "pbancNm": "ONBID sample notice for movable assets",
        "pbancStatNm": "OPEN",
        "pbancKndNm": "SALE",
        "opbdDt": "20260707",
        "opbdDtStart": "202607071000",
        "opbdDtEnd": "202607151700",
        "opengDt": "202607160930",
        "orgNm": "KAMCO",
        "deptNm": "Movable asset team",
        "dspsMthodNm": "Sale",
        "cptnMthodNm": "Online bid",
        "cltrCnt": "1",
    },
]


SAMPLE_NOTICE_DETAILS: dict[str, dict[str, Any]] = {
    "NOTICE-202607-A": {
        "pbancMngNo": "NOTICE-202607-A",
        "pbancDtlCn": "Sample notice detail payload for real estate public auction collection.",
        "dtlUrl": "https://www.onbid.co.kr/sample/notice/NOTICE-202607-A",
        "dtlDspsMthodNm": "Sale",
        "bidMthodNm": "Online bid",
    },
    "NOTICE-202607-B": {
        "pbancMngNo": "NOTICE-202607-B",
        "pbancDtlCn": "Sample notice detail payload for movable asset public auction collection.",
        "dtlUrl": "https://www.onbid.co.kr/sample/notice/NOTICE-202607-B",
        "dtlDspsMthodNm": "Sale",
        "bidMthodNm": "Online bid",
    },
}


SAMPLE_NOTICE_CLTR_ITEMS: dict[str, list[dict[str, Any]]] = {
    "NOTICE-202607-A": [
        {
            "source": "ONBID",
            "pbancMngNo": "NOTICE-202607-A",
            "onbidPbancNo": "NOTICE-202607-A",
            "cltrMngNo": "NOTICE-CLTR-202607-A-001",
            "pbctCdtnNo": "NOTICE-PBCT-001",
            "onbidCltrno": "N-CLTR-001",
            "pbctNo": "N-PBCT-001",
            "pbctNsq": "1",
            "cltrNm": "Notice linked real estate office sample",
            "prptDivNm": "Real estate",
            "dspsMthodNm": "Sale",
            "cptnMthodNm": "Online bid",
            "cltrRadr": "Seoul Jongno-gu sample 1",
            "apslEvlAmt": "320000000",
            "lowstBidPrcIndctCont": "250000000",
            "bidGrntAmt": "25000000",
            "cltrBidBgngDt": "202607060900",
            "cltrBidEndDt": "202607121800",
            "opengDt": "202607130900",
            "pbctStatNm": "OPEN",
            "orgNm": "KAMCO",
            "cltrEtcCont": "Notice item API sample attached to NOTICE-202607-A.",
        },
        {
            "source": "ONBID",
            "pbancMngNo": "NOTICE-202607-A",
            "onbidPbancNo": "NOTICE-202607-A",
            "cltrMngNo": "NOTICE-CLTR-202607-A-002",
            "pbctCdtnNo": "NOTICE-PBCT-002",
            "onbidCltrno": "N-CLTR-002",
            "pbctNo": "N-PBCT-002",
            "pbctNsq": "1",
            "cltrNm": "Notice linked land share sample",
            "prptDivNm": "Real estate",
            "dspsMthodNm": "Sale",
            "cptnMthodNm": "Online bid",
            "cltrRadr": "Chungnam Boryeong sample 2",
            "apslEvlAmt": "12000000",
            "lowstBidPrcIndctCont": "6000000",
            "bidGrntAmt": "600000",
            "cltrBidBgngDt": "202607070900",
            "cltrBidEndDt": "202607121800",
            "opengDt": "202607130900",
            "pbctStatNm": "OPEN",
            "orgNm": "KAMCO",
            "cltrEtcCont": "Second notice item API sample attached to NOTICE-202607-A.",
        },
    ],
    "NOTICE-202607-B": [
        {
            "source": "ONBID",
            "pbancMngNo": "NOTICE-202607-B",
            "onbidPbancNo": "NOTICE-202607-B",
            "cltrMngNo": "NOTICE-CLTR-202607-B-001",
            "pbctCdtnNo": "NOTICE-PBCT-003",
            "onbidCltrno": "N-CLTR-003",
            "pbctNo": "N-PBCT-003",
            "pbctNsq": "1",
            "cltrNm": "Notice linked vehicle sample",
            "prptDivNm": "Movable",
            "dspsMthodNm": "Sale",
            "cptnMthodNm": "Online bid",
            "cltrRadr": "Goyang storage sample",
            "apslEvlAmt": "18000000",
            "lowstBidPrcIndctCont": "12600000",
            "bidGrntAmt": "1260000",
            "cltrBidBgngDt": "202607071000",
            "cltrBidEndDt": "202607151700",
            "opengDt": "202607160930",
            "pbctStatNm": "OPEN",
            "orgNm": "KAMCO",
            "cltrEtcCont": "Notice item API sample attached to NOTICE-202607-B.",
        },
    ],
}


class OnbidClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    def fetch_real_estate_items(
        self,
        *,
        limit: int = 20,
        sample: bool = False,
        page_no: int = 1,
        prpt_div_cd: str = "0007,0010,0005,0002,0003,0006,0008,0011,0013",
        pvct_trgt_yn: str = "N",
        include_details: bool = False,
    ) -> tuple[list[dict[str, Any]], OnbidSyncResult]:
        if sample or not self.settings.onbid_api_key:
            items = SAMPLE_REAL_ESTATE_ITEMS[:limit]
            if include_details:
                items = [merge_onbid_detail(item, SAMPLE_REAL_ESTATE_DETAILS.get(item["cltrMngNo"], {})) for item in items]
            return items, OnbidSyncResult(fetched=len(items), source="sample", used_sample=True, total_count=len(items))

        raw_items, total_count = self._fetch_real_estate_items_from_api(
            limit=limit,
            page_no=page_no,
            prpt_div_cd=prpt_div_cd,
            pvct_trgt_yn=pvct_trgt_yn,
        )
        if include_details:
            raw_items = [self._attach_real_estate_detail(item) for item in raw_items]
        normalized = [normalize_onbid_api_item(item, source_api="real_estate_list") for item in raw_items]
        return normalized, OnbidSyncResult(
            fetched=len(normalized),
            source="onbid_api",
            used_sample=False,
            total_count=total_count,
        )

    def fetch_movable_items(
        self,
        *,
        limit: int = 20,
        sample: bool = False,
        page_no: int = 1,
        include_details: bool = False,
    ) -> tuple[list[dict[str, Any]], OnbidSyncResult]:
        if sample or not self.settings.onbid_api_key:
            items = SAMPLE_MOVABLE_ITEMS[:limit]
            if include_details:
                items = [
                    merge_onbid_detail(
                        item,
                        self.fetch_movable_detail(
                            cltr_mng_no=str(item.get("cltrMngNo") or ""),
                            pbct_cdtn_no=str(item.get("pbctCdtnNo") or ""),
                            sample=True,
                        ),
                    )
                    for item in items
                ]
            return items, OnbidSyncResult(fetched=len(items), source="sample", used_sample=True, total_count=len(items))
        raw_items, total_count = self._fetch_movable_items_from_api(limit=limit, page_no=page_no)
        if include_details:
            raw_items = [self._attach_movable_detail(item) for item in raw_items]
        normalized = [normalize_onbid_api_item(item, default_asset_type="동산", source_api="movable_list") for item in raw_items]
        return normalized, OnbidSyncResult(
            fetched=len(normalized),
            source="onbid_api",
            used_sample=False,
            total_count=total_count,
        )

    def fetch_real_estate_detail(
        self,
        *,
        cltr_mng_no: str,
        pbct_cdtn_no: str = "",
        onbid_cltr_no: str = "",
        pbct_no: str = "",
        pbct_nsq: str = "",
        sample: bool = False,
    ) -> dict[str, Any]:
        if sample or not self.settings.onbid_api_key:
            return SAMPLE_REAL_ESTATE_DETAILS.get(cltr_mng_no, {})
        base_url = self.settings.onbid_real_estate_detail_base_url.strip()
        operation = self.settings.onbid_real_estate_detail_operation.strip() or DEFAULT_REAL_ESTATE_DETAIL_OPERATION
        if not base_url:
            base_url = DEFAULT_REAL_ESTATE_DETAIL_BASE_URL
        raw_items, _ = self._fetch_onbid_items(
            base_url=base_url,
            operation=operation,
            params={
                "cltrMngNo": cltr_mng_no,
                "pbctCdtnNo": pbct_cdtn_no,
                "onbidCltrno": onbid_cltr_no,
                "pbctNo": pbct_no,
                "pbctNsq": pbct_nsq,
            },
            limit=1,
            page_no=1,
        )
        return raw_items[0] if raw_items else {}

    def fetch_movable_detail(
        self,
        *,
        cltr_mng_no: str,
        pbct_cdtn_no: str = "",
        onbid_cltr_no: str = "",
        pbct_no: str = "",
        pbct_nsq: str = "",
        sample: bool = False,
    ) -> dict[str, Any]:
        if sample or not self.settings.onbid_api_key:
            return next((item for item in SAMPLE_MOVABLE_ITEMS if item.get("cltrMngNo") == cltr_mng_no), {})
        raw_items, _ = self._fetch_onbid_items(
            base_url=self.settings.onbid_movable_detail_base_url or DEFAULT_MOVABLE_DETAIL_BASE_URL,
            operation=self.settings.onbid_movable_detail_operation or DEFAULT_MOVABLE_DETAIL_OPERATION,
            params={
                "cltrMngNo": cltr_mng_no,
                "pbctCdtnNo": pbct_cdtn_no,
                "onbidCltrno": onbid_cltr_no,
                "pbctNo": pbct_no,
                "pbctNsq": pbct_nsq,
            },
            limit=1,
            page_no=1,
        )
        return raw_items[0] if raw_items else {}

    def fetch_notice_items(
        self,
        *,
        limit: int = 20,
        page_no: int = 1,
        sample: bool = False,
        cltr_type_cd: str = "0001",
        prpt_div_cd: str = "0007,0010,0005,0002,0003,0006,0008,0011,0013",
        opbd_dt_start: str = "",
        opbd_dt_end: str = "",
        extra_filters: dict[str, Any] | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        if sample or not self.settings.onbid_api_key:
            return SAMPLE_NOTICE_ITEMS[:limit], len(SAMPLE_NOTICE_ITEMS)
        params = {
            "cltrTypeCd": cltr_type_cd,
            "prptDivCd": prpt_div_cd,
            "opbdDtStart": opbd_dt_start,
            "opbdDtEnd": opbd_dt_end,
        }
        if extra_filters:
            params.update(extra_filters)
        return self._fetch_onbid_items(
            base_url=self.settings.onbid_notice_list_base_url or DEFAULT_NOTICE_LIST_BASE_URL,
            operation=self.settings.onbid_notice_list_operation or DEFAULT_NOTICE_LIST_OPERATION,
            params=params,
            limit=limit,
            page_no=page_no,
        )

    def fetch_notice_detail(
        self,
        *,
        pbanc_mng_no: str,
        sample: bool = False,
    ) -> dict[str, Any]:
        if sample or not self.settings.onbid_api_key:
            return SAMPLE_NOTICE_DETAILS.get(pbanc_mng_no, {})
        raw_items, _ = self._fetch_onbid_items(
            base_url=self.settings.onbid_notice_detail_base_url or DEFAULT_NOTICE_DETAIL_BASE_URL,
            operation=self.settings.onbid_notice_detail_operation or DEFAULT_NOTICE_DETAIL_OPERATION,
            params={"pbancMngNo": pbanc_mng_no},
            limit=1,
            page_no=1,
        )
        return raw_items[0] if raw_items else {}

    def fetch_notice_cltr_items(
        self,
        *,
        pbanc_mng_no: str,
        limit: int = 100,
        page_no: int = 1,
        sample: bool = False,
    ) -> tuple[list[dict[str, Any]], int]:
        if sample or not self.settings.onbid_api_key:
            items = SAMPLE_NOTICE_CLTR_ITEMS.get(pbanc_mng_no, [])
            return items[:limit], len(items)
        return self._fetch_onbid_items(
            base_url=self.settings.onbid_notice_cltr_base_url or DEFAULT_NOTICE_CLTR_BASE_URL,
            operation=self.settings.onbid_notice_cltr_operation or DEFAULT_NOTICE_CLTR_OPERATION,
            params={"pbancMngNo": pbanc_mng_no},
            limit=limit,
            page_no=page_no,
        )

    def fetch_bid_target_items(
        self,
        *,
        params: dict[str, Any],
        limit: int = 100,
        page_no: int = 1,
    ) -> tuple[list[dict[str, Any]], int]:
        base_url = self.settings.onbid_bid_target_base_url.strip()
        operation = self.settings.onbid_bid_target_operation.strip()
        if not base_url or not operation:
            raise OnbidClientError("ONBID bid target endpoint is not configured.")
        return self._fetch_onbid_items(
            base_url=base_url,
            operation=operation,
            params=params,
            limit=limit,
            page_no=page_no,
        )

    def _fetch_real_estate_items_from_api(
        self,
        *,
        limit: int,
        page_no: int,
        prpt_div_cd: str,
        pvct_trgt_yn: str,
    ) -> tuple[list[dict[str, Any]], int]:
        return self._fetch_onbid_items(
            base_url=self.settings.onbid_api_base_url or DEFAULT_REAL_ESTATE_LIST_BASE_URL,
            operation=self.settings.onbid_api_operation or DEFAULT_REAL_ESTATE_LIST_OPERATION,
            params={
                "prptDivCd": prpt_div_cd,
                "pvctTrgtYn": pvct_trgt_yn,
            },
            limit=limit,
            page_no=page_no,
        )

    def _fetch_movable_items_from_api(self, *, limit: int, page_no: int) -> tuple[list[dict[str, Any]], int]:
        return self._fetch_onbid_items(
            base_url=self.settings.onbid_movable_api_base_url or DEFAULT_MOVABLE_LIST_BASE_URL,
            operation=self.settings.onbid_movable_list_operation or DEFAULT_MOVABLE_LIST_OPERATION,
            params={},
            limit=limit,
            page_no=page_no,
        )

    def _attach_real_estate_detail(self, item: dict[str, Any]) -> dict[str, Any]:
        detail = self.fetch_real_estate_detail(
            cltr_mng_no=str(item.get("cltrMngNo") or ""),
            pbct_cdtn_no=str(item.get("pbctCdtnNo") or ""),
            onbid_cltr_no=str(item.get("onbidCltrno") or ""),
            pbct_no=str(item.get("pbctNo") or ""),
            pbct_nsq=str(item.get("pbctNsq") or ""),
        )
        return merge_onbid_detail(item, detail)

    def _attach_movable_detail(self, item: dict[str, Any]) -> dict[str, Any]:
        detail = self.fetch_movable_detail(
            cltr_mng_no=str(item.get("cltrMngNo") or ""),
            pbct_cdtn_no=str(item.get("pbctCdtnNo") or ""),
            onbid_cltr_no=str(item.get("onbidCltrno") or ""),
            pbct_no=str(item.get("pbctNo") or ""),
            pbct_nsq=str(item.get("pbctNsq") or ""),
        )
        return merge_onbid_detail(item, detail)

    def _fetch_onbid_items(
        self,
        *,
        base_url: str,
        operation: str,
        params: dict[str, Any],
        limit: int,
        page_no: int,
    ) -> tuple[list[dict[str, Any]], int]:
        endpoint = f"{base_url.rstrip('/')}/{operation.lstrip('/')}"
        request_params = {
            "serviceKey": self.settings.onbid_api_key,
            "pageNo": str(max(1, page_no)),
            "numOfRows": str(max(1, min(limit, 100))),
            "resultType": "json",
        }
        request_params.update({key: value for key, value in params.items() if value not in (None, "")})
        url = f"{endpoint}?{urlencode(request_params)}"
        request = Request(url, headers={"User-Agent": "court-auction-platform/0.1"})
        try:
            with urlopen(request, timeout=20) as response:
                body = response.read().decode("utf-8")
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            detail = extract_onbid_error_message(body)
            raise OnbidClientError(f"ONBID HTTP {exc.code}: {detail}") from exc
        except Exception as exc:
            raise OnbidClientError(f"ONBID request failed: {exc}") from exc

        try:
            payload = json.loads(body)
        except json.JSONDecodeError as exc:
            raise OnbidClientError("ONBID returned non-JSON response") from exc

        root = payload.get("response", payload)
        header = root.get("header", {})
        result_code = str(header.get("resultCode", ""))
        if result_code and result_code != "00":
            result_msg = str(header.get("resultMsg", "UNKNOWN_ERROR"))
            raise OnbidClientError(f"ONBID resultCode={result_code} resultMsg={result_msg}")

        body_node = root.get("body", {})
        total_count = int(str(body_node.get("totalCount") or 0))
        items_node = body_node.get("items") or {}
        item_node = items_node.get("item") if isinstance(items_node, dict) else items_node
        if item_node is None:
            return [], total_count
        if isinstance(item_node, dict):
            return [item_node], total_count
        if isinstance(item_node, list):
            return [item for item in item_node if isinstance(item, dict)], total_count
        return [], total_count


def extract_onbid_error_message(body: str) -> str:
    try:
        payload = json.loads(body)
        root = payload.get("response", payload)
        header = root.get("header", {})
        code = header.get("resultCode") or payload.get("resultCode") or ""
        message = header.get("resultMsg") or payload.get("resultMsg") or ""
        if code or message:
            return f"resultCode={code} resultMsg={message}".strip()
    except Exception:
        pass
    compact = " ".join(str(body or "").split())
    return compact[:500] or "empty error body"


def onbid_datetime(value: Any) -> str:
    text = str(value or "").strip()
    if len(text) >= 12 and text[:12].isdigit():
        return f"{text[0:4]}-{text[4:6]}-{text[6:8]} {text[8:10]}:{text[10:12]}"
    if len(text) >= 8 and text[:8].isdigit():
        return f"{text[0:4]}-{text[4:6]}-{text[6:8]}"
    return text


def onbid_address(item: dict[str, Any]) -> str:
    direct = str(item.get("address") or item.get("cltrRadr") or "").strip()
    if direct:
        return " ".join(direct.split())
    parts = [
        str(item.get("lctnSdnm") or "").strip(),
        str(item.get("lctnSggnm") or "").strip(),
        str(item.get("lctnEmdNm") or "").strip(),
    ]
    return " ".join(part for part in parts if part)


def first_value(item: dict[str, Any], *keys: str, default: Any = "") -> Any:
    for key in keys:
        value = item.get(key)
        if value not in (None, ""):
            return value
    return default


def merge_onbid_detail(list_item: dict[str, Any], detail_item: dict[str, Any]) -> dict[str, Any]:
    if not detail_item:
        return list_item
    merged = dict(list_item)
    for key, value in detail_item.items():
        if value not in (None, ""):
            merged[key] = value
    merged["_raw_list"] = list_item
    merged["_raw_detail"] = detail_item
    return merged


def normalize_onbid_api_item(
    item: dict[str, Any],
    *,
    default_asset_type: str = "부동산",
    source_api: str = "real_estate_list",
) -> dict[str, Any]:
    return {
        "source": "ONBID",
        "cltrMngNo": first_value(item, "cltrMngNo", "cltrNo"),
        "pbctCdtnNo": first_value(item, "pbctCdtnNo", "pbctCdtnNoNm"),
        "pbancMngNo": first_value(item, "onbidPbancNo", "pbancMngNo", "pbancNo"),
        "onbidCltrno": first_value(item, "onbidCltrno", "onbidCltrNo"),
        "pbctNo": first_value(item, "pbctNo"),
        "pbctNsq": first_value(item, "pbctNsq"),
        "itemName": first_value(item, "onbidCltrNm", "cltrNm", "itemName"),
        "assetType": first_value(item, "prptDivNm", "cltrUsgLclsCtgrNm", "assetType", default=default_asset_type),
        "disposalMethod": first_value(item, "dspsMthodNm", "dtlDspsMthodNm", "disposalMethod"),
        "bidMethod": first_value(item, "cptnMthodNm", "bidDivNm", "bidMthodNm", "bidMethod"),
        "address": onbid_address(item),
        "appraisalPrice": first_value(item, "apslEvlAmt", "appraisalPrice", default=0),
        "minimumBidPrice": first_value(item, "lowstBidPrcIndctCont", "minimumBidPrice", default=0),
        "bidDeposit": first_value(item, "bidGrntAmt", "bidDeposit", default=0),
        "bidStartAt": onbid_datetime(first_value(item, "cltrBidBgngDt", "bidStartAt")),
        "bidEndAt": onbid_datetime(first_value(item, "cltrBidEndDt", "bidEndAt")),
        "openBidAt": onbid_datetime(first_value(item, "opengDt", "openBidAt")),
        "status": first_value(item, "pbctStatNm", "status"),
        "agencyName": first_value(item, "orgNm", "rqstOrgNm", "agencyName"),
        "photoUrl": first_value(item, "thnlImgUrlAdr", "photoUrl"),
        "landArea": first_value(item, "landSqms", "landArea"),
        "buildingArea": first_value(item, "bldSqms", "buildingArea"),
        "landCategory": first_value(item, "cltrUsgSclsCtgrNm", "landCategory"),
        "usage": first_value(item, "cltrUsgMclsCtgrNm", "cltrUsgLclsCtgrNm", "usage"),
        "itemDescription": first_value(item, "itemDescription", "cltrEtcCont", "rightAnalysisNote"),
        "bidCondition": first_value(item, "bidCondition", "evcRsbyTrgtCont"),
        "contractCondition": first_value(item, "contractCondition"),
        "cautions": first_value(item, "cautions", "dtbtRqrEdtmCont", "rightAnalysisNote"),
        "attachmentSummary": first_value(item, "attachmentSummary", default="온비드 API 원문 참조"),
        "noticeTitle": first_value(item, "noticeTitle", "onbidCltrNm", "cltrNm"),
        "noticeBody": first_value(item, "noticeBody", "cltrEtcCont", "itemDescription"),
        "_source_api": source_api,
        "_raw": item,
    }
