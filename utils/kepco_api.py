import json
import os
import time
import requests
from typing import Dict, List, Optional, Tuple
import random

class KEPCOService:
    """한전 신재생에너지 접속가능 용량 조회 서비스"""
    
    def __init__(self):
        self.api_key = os.getenv("KEPCO_API_KEY", "")
        self.base_url = "https://online.kepco.co.kr/ew/cpct/"
        self.mock_data_path = "data/mock_data.json"
        
    def query_connection_capacity(
        self, 
        region: str, 
        substation: str, 
        distribution_line: str = "", 
        capacity_range: Tuple[int, int] = (0, 50000),
        connection_types: Optional[List[str]] = None
    ) -> Optional[List[Dict]]:
        """
        접속가능 용량 조회
        
        Args:
            region: 지역본부
            substation: 변전소명
            distribution_line: 배전선로명 (선택)
            capacity_range: 용량 범위 (최소, 최대)
            connection_types: 신재생에너지 유형 목록
            
        Returns:
            조회 결과 리스트 또는 None
        """
        try:
            # 실제 환경에서는 KEPCO API 호출
            if self.api_key and self.api_key != "":
                return self._call_kepco_api(region, substation, distribution_line, capacity_range, connection_types)
            else:
                # 개발/테스트 환경에서는 모의 데이터 사용
                return self._generate_mock_response(region, substation, distribution_line, capacity_range, connection_types)
                
        except Exception as e:
            print(f"KEPCO API 호출 오류: {str(e)}")
            return None
    
    def _call_kepco_api(
        self, 
        region: str, 
        substation: str, 
        distribution_line: str,
        capacity_range: Tuple[int, int],
        connection_types: List[str]
    ) -> Optional[List[Dict]]:
        """실제 KEPCO API 호출"""
        
        try:
            # 변전소별 주소 매핑 (실제 KEPCO 시스템에서는 변전소명으로 직접 검색이 불가능하므로 주소 기반 검색 사용)
            substation_address_map = self._get_substation_address_mapping()
            
            # 선택된 변전소에 해당하는 주소 정보 가져오기
            address_info = substation_address_map.get(substation, None)
            
            if not address_info:
                # 기본 주소 사용 (전주변전소)
                address_info = {
                    "do": "전북특별자치도",
                    "si": "전주시", 
                    "gu": "덕진구",
                    "lidong": "강흥동",
                    "li": "춘포리",
                    "jibun": "553-5"
                }
            
            search_params = {
                "searchCondition": "address",
                **address_info
            }
            
            # 최종 용량 정보 조회
            capacity_result = self._retrieve_mesh_no(search_params)
            
            if capacity_result:
                return self._format_api_response(capacity_result)
            else:
                return None
                
        except Exception as e:
            print(f"KEPCO API 호출 오류: {str(e)}")
            return None
    
    def _get_address_init(self) -> Optional[Dict]:
        """주소 초기화 API 호출"""
        try:
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            response = requests.post(
                f"{self.base_url}retrieveAddrInit",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
                
        except requests.RequestException:
            return None
    
    def _retrieve_mesh_no(self, search_params: Dict) -> Optional[Dict]:
        """최종 용량 정보 조회 API"""
        try:
            headers = {
                "Content-Type": "application/json; charset=UTF-8",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            payload = {
                "dma_reqParam": search_params
            }
            
            response = requests.post(
                f"{self.base_url}retrieveMeshNo",
                headers=headers,
                json=payload,
                timeout=15
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
                
        except requests.RequestException:
            return None
    
    def _format_api_response(self, api_response: Dict) -> List[Dict]:
        """KEPCO API 응답을 표준 형식으로 변환"""
        formatted_results = []
        
        if "dlt_resultList" in api_response:
            for result in api_response["dlt_resultList"]:
                # 여유용량 값들 추출 (최종접속가능용량 계산용)
                vol_1 = int(result.get('VOL_1', 0))  # 변전소 여유용량
                vol_2 = int(result.get('VOL_2', 0))  # 주변압기 여유용량
                vol_3 = int(result.get('VOL_3', 0))  # 배전선로 여유용량
                
                # 최종 접속가능용량은 변전소→주변압기→배전선로 중 최소값
                final_capacity = min([v for v in [vol_1, vol_2, vol_3] if v > 0], default=0)
                final_status = "정상" if final_capacity > 0 else "포화"
                
                # 변전소 정보
                subst_capa = int(result.get('SUBST_CAPA', 0))
                g_subst_capa = int(result.get('G_SUBST_CAPA', 0))
                subst_calculated_capacity = subst_capa - g_subst_capa if subst_capa > 0 and g_subst_capa > 0 else 0
                
                formatted_result = {
                    "변전소": f"{result.get('SUBST_NM', '')}변전소",
                    "주변압기": "-",
                    "배전선로": "-",
                    "접속기준용량(kW)": subst_capa,
                    "접수기준접속용량(kW)": int(result.get('SUBST_PWR', 0)),
                    "접속계획반영접속용량(kW)": g_subst_capa,
                    "여유용량(kW)": f"{vol_1:,}",
                    "접속계획반영여유용량(kW)": f"{subst_calculated_capacity:,}",
                    "최종접속가능용량": f"{final_capacity:,}",
                    "상태": final_status,
                    "여유용량비율(%)": round((vol_1 / max(subst_capa, 1)) * 100, 1),
                    # 원본 API 필드 보존
                    "SUBST_CAPA": subst_capa,
                    "G_SUBST_CAPA": g_subst_capa,
                    "SUBST_PWR": int(result.get('SUBST_PWR', 0)),
                    "VOL_1": vol_1
                }
                formatted_results.append(formatted_result)
                
                # 주변압기 정보가 있는 경우 추가
                if result.get('MTR_CAPA') and int(result.get('MTR_CAPA', 0)) > 0:
                    mtr_capa = int(result.get('MTR_CAPA', 0))
                    g_mtr_capa = int(result.get('G_MTR_CAPA', 0))
                    mtr_calculated_capacity = mtr_capa - g_mtr_capa if mtr_capa > 0 and g_mtr_capa > 0 else 0
                    
                    mtr_result = {
                        "변전소": f"{result.get('SUBST_NM', '')}변전소",
                        "주변압기": f"#{result.get('MTR_NO', '-')}",
                        "배전선로": "-",
                        "접속기준용량(kW)": mtr_capa,
                        "접수기준접속용량(kW)": int(result.get('MTR_PWR', 0)),
                        "접속계획반영접속용량(kW)": g_mtr_capa,
                        "여유용량(kW)": f"{vol_2:,}",
                        "접속계획반영여유용량(kW)": f"{mtr_calculated_capacity:,}",
                        "최종접속가능용량": f"{final_capacity:,}",
                        "상태": final_status,
                        "여유용량비율(%)": round((vol_2 / max(mtr_capa, 1)) * 100, 1),
                        # 원본 API 필드 보존
                        "MTR_CAPA": mtr_capa,
                        "G_MTR_CAPA": g_mtr_capa,
                        "MTR_PWR": int(result.get('MTR_PWR', 0)),
                        "VOL_2": vol_2
                    }
                    formatted_results.append(mtr_result)
                
                # 배전선로 정보가 있는 경우 추가
                if result.get('DL_CAPA') and int(result.get('DL_CAPA', 0)) > 0:
                    dl_capa = int(result.get('DL_CAPA', 0))
                    g_dl_capa = int(result.get('G_DL_CAPA', 0))
                    dl_calculated_capacity = dl_capa - g_dl_capa if dl_capa > 0 and g_dl_capa > 0 else 0
                    
                    dl_result = {
                        "변전소": f"{result.get('SUBST_NM', '')}변전소",
                        "주변압기": f"#{result.get('MTR_NO', '-')}",
                        "배전선로": result.get('DL_NM', '-'),
                        "접속기준용량(kW)": dl_capa,
                        "접수기준접속용량(kW)": int(result.get('DL_PWR', 0)),
                        "접속계획반영접속용량(kW)": g_dl_capa,
                        "여유용량(kW)": f"{vol_3:,}",
                        "접속계획반영여유용량(kW)": f"{dl_calculated_capacity:,}",
                        "최종접속가능용량": f"{final_capacity:,}",
                        "상태": final_status,
                        "여유용량비율(%)": round((vol_3 / max(dl_capa, 1)) * 100, 1),
                        # 원본 API 필드 보존
                        "DL_CAPA": dl_capa,
                        "G_DL_CAPA": g_dl_capa,
                        "DL_PWR": int(result.get('DL_PWR', 0)),
                        "VOL_3": vol_3
                    }
                    formatted_results.append(dl_result)
        
        return formatted_results
    
    def query_by_address(
        self,
        sido: str,
        si: str,
        gu: str,
        dong: str,
        li: str = "",
        jibun: str = "",
        capacity_range: Tuple[int, int] = (0, 50000),
        connection_types: Optional[List[str]] = None
    ) -> Optional[List[Dict]]:
        """주소 기반 접속가능 용량 조회"""
        
        try:
            # 실제 환경에서는 KEPCO API 호출
            if self.api_key and self.api_key != "":
                return self._call_kepco_api_by_address(sido, si, gu, dong, li, jibun, capacity_range, connection_types)
            else:
                # 개발/테스트 환경에서는 모의 데이터 사용
                return self._generate_mock_response_by_address(sido, si, gu, dong, li, jibun, capacity_range, connection_types)
                
        except Exception as e:
            print(f"KEPCO 주소별 조회 오류: {str(e)}")
            return None
    
    def query_by_transformer_number(self, pole_number: str) -> Optional[Dict]:
        """전산화번호로 배전용(공용)변압기 용량 조회"""
        
        try:
            # 실제 환경에서는 KEPCO API 호출
            if self.api_key and self.api_key != "":
                return self._call_kepco_api_by_transformer(pole_number)
            else:
                # 개발/테스트 환경에서는 모의 데이터 사용
                return self._generate_mock_transformer_response(pole_number)
                
        except Exception as e:
            print(f"KEPCO 배전용(공용)변압기 조회 오류: {str(e)}")
            return None
    
    def _call_kepco_api_by_transformer(self, pole_number: str) -> Optional[Dict]:
        """배전용(공용)변압기 실제 KEPCO API 호출"""
        
        # TODO: 실제 KEPCO API 엔드포인트로 변압기 정보 조회
        # 현재는 모의 데이터로 대체
        return self._generate_mock_transformer_response(pole_number)
    
    def _generate_mock_transformer_response(self, pole_number: str) -> Dict:
        """배전용(공용)변압기 모의 응답 데이터 생성"""
        
        # 전산화번호에 따른 기본 설정
        transformer_configs = {
            "9185W431": {
                "pole_number": "9185W431",
                "substation": "광주전남본부",
                "branch": "나주지사",
                "available": "가용",
                "detail": "상세보기",
                "phases": {
                    "A상": {"기준용량": 100, "가설누적용량": 3, "여유용량": 28.1},
                    "B상": {"기준용량": 100, "가설누적용량": 0, "여유용량": 31.1},
                    "C상": {"기준용량": 100, "가설누적용량": 0, "여유용량": 31.1}
                },
                "warning_message": "연계용량이 500kW 미만인 경우 저압 연계 대상입니다.",
                "info_message": "여유용량 부족 시 설비 용량조회(변전소, 주변압기, 배전선로)를 통해 접촉가능여부를 확인하시기 바랍니다."
            },
            "1234W123": {
                "pole_number": "1234W123",
                "substation": "전북특별자치도본부",
                "branch": "전주지사",
                "available": "포화",
                "detail": "상세보기",
                "phases": {
                    "A상": {"기준용량": 50, "가설누적용량": 45, "여유용량": 5.0},
                    "B상": {"기준용량": 50, "가설누적용량": 48, "여유용량": 2.0},
                    "C상": {"기준용량": 50, "가설누적용량": 50, "여유용량": 0.0}
                },
                "warning_message": "연계용량이 500kW 미만인 경우 저압 연계 대상입니다.",
                "info_message": "여유용량 부족 시 설비 용량조회(변전소, 주변압기, 배전선로)를 통해 접촉가능여부를 확인하시기 바랍니다."
            }
        }
        
        # 기본 변압기 정보 설정 (입력된 번호가 없는 경우)
        default_config = {
            "pole_number": pole_number,
            "substation": "전북특별자치도본부",
            "branch": "전주지사",
            "available": "가용",
            "detail": "상세보기",
            "phases": {
                "A상": {"기준용량": 75, "가설누적용량": 15, "여유용량": 20.5},
                "B상": {"기준용량": 75, "가설누적용량": 12, "여유용량": 23.0},
                "C상": {"기준용량": 75, "가설누적용량": 18, "여유용량": 19.2}
            },
            "warning_message": "연계용량이 500kW 미만인 경우 저압 연계 대상입니다.",
            "info_message": "여유용량 부족 시 설비 용량조회(변전소, 주변압기, 배전선로)를 통해 접촉가능여부를 확인하시기 바랍니다."
        }
        
        return transformer_configs.get(pole_number, default_config)
    
    def _call_kepco_api_by_address(
        self,
        sido: str,
        si: str,
        gu: str,
        dong: str,
        li: str,
        jibun: str,
        capacity_range: Tuple[int, int],
        connection_types: List[str]
    ) -> Optional[List[Dict]]:
        """주소 기반 실제 KEPCO API 호출"""
        
        search_params = {
            "searchCondition": "address",
            "do": sido,
            "si": si,
            "gu": gu,
            "lidong": dong,
            "li": li,
            "jibun": jibun
        }
        
        # 최종 용량 정보 조회
        capacity_result = self._retrieve_mesh_no(search_params)
        
        if capacity_result:
            return self._format_api_response(capacity_result)
        else:
            return None
    
    def _generate_mock_response_by_address(
        self,
        sido: str,
        si: str,
        gu: str,
        dong: str,
        li: str,
        jibun: str,
        capacity_range: Tuple[int, int],
        connection_types: List[str]
    ) -> List[Dict]:
        """주소 기반 개발용 모의 응답 생성"""
        
        # 지연 시뮬레이션 (실제 API 호출과 유사한 경험)
        time.sleep(1.5)
        
        # 전북 전주시 덕진구 강흥동 예시 데이터
        if "전주" in si and "덕진" in gu and "강흥" in dong:
            # 최종접속가능용량은 변전소(98,496), 주변압기(10,741), 배전선로(0) 중 최소값 = 0
            final_capacity = 0
            final_status = "포화"
            
            return [
                {
                    "변전소": "전주변전소",
                    "주변압기": "-",
                    "배전선로": "-",
                    "접속기준용량(kW)": 200000,
                    "접수기준접속용량(kW)": 101504,
                    "접속계획반영접속용량(kW)": 94381,
                    "여유용량(kW)": "98,496",
                    "접속계획반영여유용량(kW)": "105,619",
                    "최종접속가능용량": f"{final_capacity:,}",
                    "상태": final_status,
                    "여유용량비율(%)": 49.2,
                    # 원본 API 필드
                    "SUBST_CAPA": 200000,
                    "G_SUBST_CAPA": 94381,
                    "SUBST_PWR": 101504,
                    "VOL_1": 98496
                },
                {
                    "변전소": "전주변전소",
                    "주변압기": "#3",
                    "배전선로": "-",
                    "접속기준용량(kW)": 50000,
                    "접수기준접속용량(kW)": 39259,
                    "접속계획반영접속용량(kW)": 35665,
                    "여유용량(kW)": "10,741",
                    "접속계획반영여유용량(kW)": "14,335",
                    "최종접속가능용량": f"{final_capacity:,}",
                    "상태": final_status,
                    "여유용량비율(%)": 21.5,
                    # 원본 API 필드
                    "MTR_CAPA": 50000,
                    "G_MTR_CAPA": 35665,
                    "MTR_PWR": 39259,
                    "VOL_2": 10741
                },
                {
                    "변전소": "전주변전소",
                    "주변압기": "#3",
                    "배전선로": "이서",
                    "접속기준용량(kW)": 12000,
                    "접수기준접속용량(kW)": 14915,
                    "접속계획반영접속용량(kW)": 14314,
                    "여유용량(kW)": "0",
                    "접속계획반영여유용량(kW)": "-2,314",
                    "최종접속가능용량": f"{final_capacity:,}",
                    "상태": final_status,
                    "여유용량비율(%)": 0.0,
                    # 원본 API 필드
                    "DL_CAPA": 12000,
                    "G_DL_CAPA": 14314,
                    "DL_PWR": 14915,
                    "VOL_3": 0
                }
            ]
        else:
            # 다른 지역의 예시 데이터
            return [
                {
                    "변전소": f"{si.replace('시', '')}변전소",
                    "주변압기": "-",
                    "배전선로": "-",
                    "접속기준용량(kW)": random.randint(80000, 150000),
                    "접수기준접속용량(kW)": random.randint(60000, 120000),
                    "접속계획반영접속용량(kW)": random.randint(55000, 110000),
                    "여유용량(kW)": f"{random.randint(5000, 25000):,}/{random.randint(8000, 30000):,}",
                    "상태": "정상",
                    "여유용량비율(%)": round(random.uniform(5.0, 25.0), 1)
                }
            ]
    
    def _generate_mock_response(
        self, 
        region: str, 
        substation: str, 
        distribution_line: str,
        capacity_range: Tuple[int, int],
        connection_types: List[str]
    ) -> List[Dict]:
        """개발용 모의 응답 생성 - 변전소별 주소 매핑 기반"""
        
        # 지연 시뮬레이션 (실제 API 호출과 유사한 경험)
        time.sleep(1.5)
        
        # 변전소별 주소 매핑을 통한 실제 주소 기반 검색 시뮬레이션
        substation_address_map = self._get_substation_address_mapping()
        address_info = substation_address_map.get(substation, None)
        
        if address_info:
            # 매핑된 주소로 주소 기반 검색 시뮬레이션
            return self._generate_mock_response_by_address(
                address_info["do"],
                address_info["si"], 
                address_info["gu"],
                address_info["lidong"],
                address_info["li"],
                address_info["jibun"],
                capacity_range,
                connection_types or []
            )
        else:
            # 매핑되지 않은 변전소의 경우 일반적인 데이터 생성
            final_capacity = random.randint(5000, 25000)
            status = "정상" if final_capacity > 1000 else "포화"
            
            return [
                {
                    "변전소": substation,
                    "변전소코드": f"SUBST_{random.randint(1000, 9999)}",
                    "주변압기": "-",
                    "배전선로": "-",
                    "배전선로코드": "",
                    "변전소접속기준용량": f"{random.randint(80000, 150000):,} kW",
                    "주변압기접속기준용량": "0 kW",
                    "배전선로접속기준용량": "0 kW",
                    "변전소접수기준접속용량": f"{random.randint(60000, 120000):,} kW",
                    "주변압기접수기준접속용량": "0 kW",
                    "배전선로접수기준접속용량": "0 kW",
                    "변전소여유용량": f"{final_capacity:,} kW",
                    "주변압기여유용량": "0 kW",
                    "배전선로여유용량": "0 kW",
                    "변전소접속계획반영접속용량": f"{random.randint(55000, 110000):,} kW",
                    "주변압기접속계획반영접속용량": "0 kW",
                    "배전선로접속계획반영접속용량": "0 kW",
                    "최종접속가능용량": final_capacity,
                    "상태": status,
                    # 원본 API 데이터
                    "SUBST_CAPA": random.randint(80000, 150000),
                    "SUBST_PWR": random.randint(60000, 120000),
                    "MTR_CAPA": 0,
                    "MTR_PWR": 0,
                    "DL_CAPA": 0,
                    "DL_PWR": 0,
                    "VOL_1": final_capacity,
                    "VOL_2": 0,
                    "VOL_3": 0,
                    "G_SUBST_CAPA": random.randint(55000, 110000),
                    "G_MTR_CAPA": 0,
                    "G_DL_CAPA": 0
                }
            ]
    
    def _get_substation_address_mapping(self) -> Dict[str, Dict[str, str]]:
        """변전소별 주소 매핑 정보"""
        return {
            # 전북본부
            "전주변전소": {
                "do": "전북특별자치도",
                "si": "전주시",
                "gu": "덕진구", 
                "lidong": "강흥동",
                "li": "춘포리",
                "jibun": "553-5"
            },
            "익산변전소": {
                "do": "전북특별자치도",
                "si": "익산시",
                "gu": "익산시",
                "lidong": "영등동",
                "li": "",
                "jibun": "100"
            },
            "군산변전소": {
                "do": "전북특별자치도", 
                "si": "군산시",
                "gu": "군산시",
                "lidong": "경암동",
                "li": "",
                "jibun": "200"
            },
            "정읍변전소": {
                "do": "전북특별자치도",
                "si": "정읍시", 
                "gu": "정읍시",
                "lidong": "시기동",
                "li": "",
                "jibun": "300"
            },
            
            # 서울본부  
            "강남변전소": {
                "do": "서울특별시",
                "si": "강남구",
                "gu": "강남구",
                "lidong": "역삼동",
                "li": "",
                "jibun": "100"
            },
            "강북변전소": {
                "do": "서울특별시",
                "si": "강북구", 
                "gu": "강북구",
                "lidong": "미아동",
                "li": "",
                "jibun": "200"
            },
            "강서변전소": {
                "do": "서울특별시",
                "si": "강서구",
                "gu": "강서구", 
                "lidong": "화곡동",
                "li": "",
                "jibun": "300"
            },
            "강동변전소": {
                "do": "서울특별시",
                "si": "강동구",
                "gu": "강동구",
                "lidong": "천호동", 
                "li": "",
                "jibun": "400"
            },
            "용산변전소": {
                "do": "서울특별시",
                "si": "용산구",
                "gu": "용산구",
                "lidong": "한강로동",
                "li": "",
                "jibun": "500"
            },
            
            # 경기본부
            "수원변전소": {
                "do": "경기도",
                "si": "수원시",
                "gu": "영통구",
                "lidong": "매탄동",
                "li": "",
                "jibun": "100"
            },
            "성남변전소": {
                "do": "경기도", 
                "si": "성남시",
                "gu": "분당구",
                "lidong": "정자동",
                "li": "",
                "jibun": "200"
            },
            "고양변전소": {
                "do": "경기도",
                "si": "고양시",
                "gu": "일산동구", 
                "lidong": "장항동",
                "li": "",
                "jibun": "300"
            },
            "안양변전소": {
                "do": "경기도",
                "si": "안양시",
                "gu": "만안구",
                "lidong": "안양동",
                "li": "",
                "jibun": "400"
            },
            "의정부변전소": {
                "do": "경기도",
                "si": "의정부시",
                "gu": "의정부시",
                "lidong": "의정부동",
                "li": "",
                "jibun": "500"
            }
        }
    
    def _load_mock_data(self) -> Dict:
        """모의 데이터 로드"""
        try:
            with open(self.mock_data_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def validate_query_params(
        self, 
        region: str, 
        substation: str, 
        capacity_range: Tuple[int, int]
    ) -> Tuple[bool, str]:
        """조회 파라미터 유효성 검사"""
        
        if not region or not substation:
            return False, "지역본부와 변전소를 선택해주세요."
        
        if capacity_range[0] < 0 or capacity_range[1] <= capacity_range[0]:
            return False, "올바른 용량 범위를 설정해주세요."
        
        if capacity_range[1] > 100000:
            return False, "조회 가능한 최대 용량은 100,000 kW입니다."
        
        return True, ""
    
    def get_substation_info(self, region: str, substation: str) -> Optional[Dict]:
        """변전소 상세 정보 조회"""
        mock_data = self._load_mock_data()
        
        if region in mock_data.get("regions", {}):
            substations = mock_data["regions"][region].get("substations", {})
            return substations.get(substation)
        
        return None
    
    def get_renewable_type_info(self, renewable_type: str) -> Optional[Dict]:
        """신재생에너지 유형별 정보 조회"""
        mock_data = self._load_mock_data()
        return mock_data.get("renewable_types", {}).get(renewable_type)
    
    def get_address_data(self, gbn: int, addr_do: str = "", addr_si: str = "", addr_gu: str = "", addr_lidong: str = "") -> Optional[List[Dict]]:
        """주소 데이터 조회 (시/도, 시/군, 구/군, 동/면, 리, 번지)"""
        try:
            headers = {
                "Content-Type": "application/json; charset=UTF-8",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            if gbn == -1:  # 시/도 데이터 조회
                response = requests.post(
                    f"{self.base_url}retrieveAddrInit",
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("dlt_sido", [])
            else:
                # 나머지 주소 단계 조회
                payload = {
                    "dma_addrGbn": {
                        "gbn": gbn,
                        "addr_do": addr_do,
                        "addr_si": addr_si,
                        "addr_gu": addr_gu,
                        "addr_lidong": addr_lidong,
                        "addr_li": "",
                        "addr_jibun": ""
                    }
                }
                
                response = requests.post(
                    f"{self.base_url}retrieveAddrGbn",
                    headers=headers,
                    json=payload,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("dlt_addrGbn", [])
            
            return None
            
        except requests.RequestException as e:
            print(f"주소 데이터 조회 오류: {str(e)}")
            return None
    
    def retrieve_mesh_capacity(self, search_condition: str = "address", addr_do: str = "", addr_si: str = "", 
                              addr_gu: str = "", addr_lidong: str = "", addr_li: str = "", addr_jibun: str = "") -> Optional[List[Dict]]:
        """신·재생e 접속가능 용량 조회"""
        try:
            headers = {
                "Content-Type": "application/json; charset=UTF-8",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json",
                "Origin": "https://online.kepco.co.kr",
                "Referer": "https://online.kepco.co.kr/EWM092D00"
            }
            
            payload = {
                "dma_reqParam": {
                    "searchCondition": search_condition,
                    "do": addr_do,
                    "si": addr_si,
                    "gu": addr_gu,
                    "lidong": addr_lidong,
                    "li": addr_li,
                    "jibun": addr_jibun
                }
            }
            
            response = requests.post(
                f"{self.base_url}retrieveMeshNo",
                headers=headers,
                json=payload,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("dlt_resultList", [])
            else:
                print(f"API 호출 실패: {response.status_code}")
                return None
            
        except requests.RequestException as e:
            print(f"용량 조회 오류: {str(e)}")
            return None
