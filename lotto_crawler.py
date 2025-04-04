import logging
import requests
from bs4 import BeautifulSoup
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time
import re

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    filename='lotto_crawler.log',
    filemode='a'
)

# 상수 정의
LOTTO_URL = "https://www.dhlottery.co.kr/gameResult.do?method=byWin&drwNo="
SPREADSHEET_NAME = "로또당첨번호"
SHEET_NAMES = {
    "1호기": "1호기당첨번호",
    "2호기": "2호기당첨번호",
    "3호기": "3호기당첨번호"
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

def get_or_create_sheet(client, sheet_name):
    """시트 가져오기 또는 생성"""
    try:
        # 스프레드시트 열기
        spreadsheet = client.open(SPREADSHEET_NAME)
        
        # 시트 존재 여부 확인
        try:
            sheet = spreadsheet.worksheet(sheet_name)
            logging.info(f"'{sheet_name}' 시트를 찾았습니다.")
        except gspread.exceptions.WorksheetNotFound:
            # 시트가 없으면 생성
            sheet = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=20)
            # 헤더 추가
            headers = ['회차', '추첨일', '번호1', '번호2', '번호3', '번호4', '번호5', '번호6']
            sheet.append_row(headers)
            logging.info(f"'{sheet_name}' 시트를 생성했습니다.")
        
        return sheet
    except Exception as e:
        logging.error(f"시트 가져오기 또는 생성 실패: {e}")
        return None

def fetch_lottery_data(draw_number):
    """로또 당첨 번호 데이터 가져오기"""
    try:
        url = f"{LOTTO_URL}{draw_number}"
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 추첨일 추출
        date_element = soup.select_one('div.win_result > h4 > span')
        if not date_element:
            logging.warning(f"회차 {draw_number}의 추첨일 정보를 찾을 수 없습니다.")
            return None
        
        draw_date = date_element.text.strip().replace('(', '').replace(')', '')
        match = re.search(r'\d{4}\.\d{2}\.\d{2}', draw_date)
        if match:
            draw_date = match.group()
        else:
            logging.warning(f"회차 {draw_number}의 추첨일 형식이 올바르지 않습니다: {draw_date}")
            return None
        
        # 당첨 번호 추출
        number_elements = soup.select('div.win_result > div > div.num.win > p > span.ball_645')
        if not number_elements or len(number_elements) != 6:
            logging.warning(f"회차 {draw_number}의 당첨 번호를 찾을 수 없습니다.")
            return None
        
        numbers = [int(element.text.strip()) for element in number_elements]
        
        return {
            'draw_number': draw_number,
            'draw_date': draw_date,
            'numbers': numbers
        }
    except Exception as e:
        logging.error(f"회차 {draw_number} 데이터 가져오기 실패: {e}")
        return None

def update_sheet_data(sheet, data):
    """시트 데이터 업데이트"""
    try:
        # 회차 데이터가 이미 있는지 확인
        existing_data = sheet.get_all_values()
        draw_numbers = [row[0] for row in existing_data[1:] if row and row[0].isdigit()]
        
        if str(data['draw_number']) in draw_numbers:
            logging.info(f"회차 {data['draw_number']}는 이미 존재합니다. 건너뜁니다.")
            return True
        
        # 새 데이터 추가
        row_data = [
            data['draw_number'], 
            data['draw_date'], 
            data['numbers'][0],
            data['numbers'][1],
            data['numbers'][2],
            data['numbers'][3],
            data['numbers'][4],
            data['numbers'][5]
        ]
        
        sheet.append_row(row_data)
        logging.info(f"회차 {data['draw_number']} 데이터를 추가했습니다.")
        return True
    except Exception as e:
        logging.error(f"시트 데이터 업데이트 실패: {e}")
        return False

def determine_machine_type(draw_number):
    """추첨 기기 결정 (임의의 로직)"""
    # 실제로는 공식 정보에 따라 결정해야 함
    # 여기서는 예시로 회차 번호를 3으로 나눈 나머지에 따라 결정
    remainder = int(draw_number) % 3
    if remainder == 0:
        return "3호기"
    elif remainder == 1:
        return "1호기"
    else:
        return "2호기"

def main():
    """메인 함수"""
    try:
        # Google API 연결
        client = connect_to_google_sheets()
        if not client:
            return
        
        # 각 호기별 시트 준비
        sheets = {}
        for machine_type, sheet_name in SHEET_NAMES.items():
            sheet = get_or_create_sheet(client, sheet_name)
            if sheet:
                sheets[machine_type] = sheet
        
        # 최신 회차부터 과거 회차까지 데이터 수집
        latest_draw = 1165  # 최신 회차
        oldest_draw = 900   # 수집할 가장 오래된 회차
        
        for draw_number in range(latest_draw, oldest_draw-1, -1):
            data = fetch_lottery_data(draw_number)
            if data:
                # 추첨 기기 결정
                machine_type = determine_machine_type(draw_number)
                
                # 해당 호기 시트 업데이트
                if machine_type in sheets:
                    success = update_sheet_data(sheets[machine_type], data)
                    if not success:
                        logging.warning(f"회차 {draw_number} 데이터 업데이트 실패, 다음 회차로 넘어갑니다.")
                else:
                    logging.warning(f"호기 {machine_type}에 해당하는 시트가 없습니다.")
            
            # API 할당량 문제 방지를 위한 지연
            time.sleep(3)
        
        logging.info("=== 로또 크롤링 스크립트 성공적으로 완료 ===")
    except Exception as e:
        logging.error(f"오류 발생: {e}")

if __name__ == "__main__":
    main()