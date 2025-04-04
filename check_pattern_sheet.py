import logging
import sys
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# 패턴 시트 매핑
PATTERN_SHEETS = {
    "1호기": "1호기패턴",
    "2호기": "2호기패턴",
    "3호기": "3호기패턴",
    "1호기1개일치": "1호기1개일치패턴",
    "2호기1개일치": "2호기1개일치패턴",
    "3호기1개일치": "3호기1개일치패턴"
}

def connect_to_google_sheets():
    """구글 스프레드시트 API 연결"""
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        credentials = ServiceAccountCredentials.from_json_keyfile_name('loto2025-4f3fea37499a.json', scope)
        client = gspread.authorize(credentials)
        logging.info("구글 스프레드시트 API 연결 성공")
        return client
    except Exception as e:
        logging.error(f"구글 스프레드시트 API 연결 실패: {e}")
        return None

def get_pattern_sheet(client, sheet_name):
    """패턴 시트 가져오기"""
    try:
        # 스프레드시트 열기
        spreadsheet = client.open("로또당첨번호")
        
        # 시트 존재 여부 확인
        try:
            sheet = spreadsheet.worksheet(sheet_name)
            logging.info(f"'{sheet_name}' 시트를 찾았습니다.")
            return sheet
        except gspread.exceptions.WorksheetNotFound:
            logging.error(f"'{sheet_name}' 시트를 찾을 수 없습니다.")
            return None
    except Exception as e:
        logging.error(f"시트 가져오기 실패: {e}")
        return None

def check_pattern_sheet(sheet, pattern_type):
    """패턴 시트 내용 확인"""
    try:
        # 모든 데이터 가져오기
        all_values = sheet.get_all_values()
        logging.info(f"총 {len(all_values)}개 행을 가져왔습니다.")
        
        if len(all_values) < 5:
            logging.warning("시트에 충분한 데이터가 없습니다.")
            return False
        
        # 최신 회차 정보 확인
        logging.info(f"최신 회차 정보: {all_values[1]}")
        
        # 패턴 섹션 확인
        pattern_sections = {}
        
        for i, row in enumerate(all_values):
            if len(row) > 0:
                # 일치 패턴 섹션 확인
                for match_count in [5, 4, 3, 2, 1]:
                    if len(row) > 0 and f"{match_count}개 일치 패턴" in row[0]:
                        pattern_sections[match_count] = i
                        logging.info(f"{match_count}개 일치 패턴 섹션 발견 (행 {i+1})")
                        
                        # 헤더 행 및 데이터 확인
                        if i+1 < len(all_values):
                            header_row = all_values[i+1]
                            logging.info(f"헤더 행: {header_row}")
                            
                            # 데이터 행 수 확인
                            data_count = 0
                            for j in range(i+2, len(all_values)):
                                if j < len(all_values) and len(all_values[j]) > 0:
                                    if "일치 패턴" in all_values[j][0]:  # 다음 패턴 섹션 시작
                                        break
                                    data_count += 1
                            logging.info(f"{match_count}개 일치 패턴 데이터 행 수: {data_count}")
        
        # 1개 일치 패턴 확인 (1호기1개일치패턴 시트인 경우)
        if "1개일치" in pattern_type:
            if len(all_values) > 10:
                for i in range(min(5, len(all_values))):
                    logging.info(f"행 {i+1}: {all_values[i]}")
                
                # 다음 회차에 2회 이상 나온 번호 섹션 확인
                for i, row in enumerate(all_values):
                    if len(row) > 0 and "다음 회차에 2회 이상 나온 번호" in row[0]:
                        logging.info(f"다음 회차 번호 빈도 섹션 발견 (행 {i+1})")
                        break
                
                # 추천 번호 섹션 확인
                for i, row in enumerate(all_values):
                    if len(row) > 0 and "추천 번호" in row[0]:
                        logging.info(f"추천 번호 섹션 발견 (행 {i+1})")
                        if i+1 < len(all_values) and len(all_values[i+1]) > 0:
                            logging.info(f"추천 번호: {all_values[i+1][0]}")
                        break
        
        # 일반 패턴 시트인 경우 다음 회차 번호 분석 섹션 확인
        else:
            for i, row in enumerate(all_values):
                if len(row) > 0 and "다음 회차 분석" in row[0]:
                    logging.info(f"다음 회차 번호 분석 섹션 발견 (행 {i+1})")
                    break
        
        # 데이터 존재 여부 확인
        if len(pattern_sections) > 0:
            logging.info("패턴 데이터가 존재합니다.")
            return True
        else:
            logging.warning("패턴 데이터가 존재하지 않습니다.")
            return False
    except Exception as e:
        logging.error(f"패턴 시트 확인 중 오류 발생: {e}")
        return False

def main():
    """메인 함수"""
    try:
        if len(sys.argv) < 2:
            print("사용법: python check_pattern_sheet.py [1호기|2호기|3호기|1호기1개일치|2호기1개일치|3호기1개일치]")
            return
        
        pattern_type = sys.argv[1]
        if pattern_type not in PATTERN_SHEETS:
            print(f"오류: 유효하지 않은 패턴 타입입니다. {', '.join(PATTERN_SHEETS.keys())} 중 하나를 선택하세요.")
            return
        
        sheet_name = PATTERN_SHEETS[pattern_type]
        
        # Google API 연결
        client = connect_to_google_sheets()
        if not client:
            return
        
        # 패턴 시트 가져오기
        sheet = get_pattern_sheet(client, sheet_name)
        if not sheet:
            return
        
        # 패턴 시트 확인
        success = check_pattern_sheet(sheet, pattern_type)
        
        if success:
            logging.info("=== 패턴 시트 확인 스크립트 성공적으로 완료 ===")
        else:
            logging.warning("=== 패턴 시트 확인 결과 문제가 발견되었습니다 ===")
    except Exception as e:
        logging.error(f"오류 발생: {e}")

if __name__ == "__main__":
    main()