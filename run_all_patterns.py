import logging
import subprocess
import time

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def run_script(script_name):
    """스크립트 실행 함수"""
    try:
        logging.info(f"{script_name} 실행 시작")
        result = subprocess.run(['python', script_name], check=True, capture_output=True, text=True)
        logging.info(f"{script_name} 실행 완료: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"{script_name} 실행 실패: {e}")
        logging.error(f"오류 출력: {e.stderr}")
        return False

def main():
    """모든 패턴 분석 스크립트 순차 실행"""
    try:
        scripts = [
            'create_1ho_pattern.py',
            'create_2ho_pattern.py',
            'create_3ho_pattern.py'
        ]
        
        for script in scripts:
            success = run_script(script)
            if not success:
                logging.warning(f"{script} 실행 실패, 다음 스크립트로 진행합니다.")
            # API 할당량 문제 방지를 위한 지연
            time.sleep(30)
        
        logging.info("모든 패턴 분석 스크립트 실행 완료")
    except Exception as e:
        logging.error(f"실행 중 오류 발생: {e}")

if __name__ == "__main__":
    main()