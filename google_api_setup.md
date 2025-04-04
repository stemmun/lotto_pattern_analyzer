# 구글 API 설정 가이드

이 문서는 로또 패턴 분석 도구에서 필요한 구글 API 설정 방법을 안내합니다.

## 1. Google Cloud Platform 설정

1. [Google Cloud Platform](https://console.cloud.google.com/)에 로그인합니다.
2. 프로젝트를 생성합니다.
3. API 및 서비스 → 라이브러리로 이동합니다.
4. 다음 API를 활성화합니다:
   - Google Drive API
   - Google Sheets API

## 2. 서비스 계정 만들기

1. API 및 서비스 → 사용자 인증 정보로 이동합니다.
2. 사용자 인증 정보 만들기 → 서비스 계정을 선택합니다.
3. 서비스 계정 이름과 설명을 입력하고 생성합니다.
4. 역할을 부여합니다 (프로젝트 → 편집자).

## 3. 키 생성

1. 생성된 서비스 계정을 클릭합니다.
2. 키 탭으로 이동합니다.
3. 키 추가 → 새 키 만들기를 선택합니다.
4. JSON 형식을 선택하고 생성합니다.
5. 다운로드된 JSON 파일을 프로젝트 폴더에 `loto2025-4f3fea37499a.json`으로 저장합니다.

## 4. 구글 스프레드시트 공유

1. 구글 드라이브에서 스프레드시트를 생성합니다.
2. 공유 설정으로 이동합니다.
3. 서비스 계정 이메일 주소를 추가하고 편집자 권한을 부여합니다.
   - 서비스 계정 이메일은 JSON 파일 내 `client_email` 필드에서 확인할 수 있습니다.

## 5. 코드에서 사용하기

```python
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# 인증 설정
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name('loto2025-4f3fea37499a.json', scope)
client = gspread.authorize(credentials)

# 스프레드시트 접근
sheet = client.open('스프레드시트_이름').worksheet('시트_이름')
```

## 문제 해결

- **권한 오류**: 서비스 계정이 스프레드시트에 편집자 권한으로 올바르게 공유되었는지 확인하세요.
- **할당량 초과**: 구글 API는 분당 요청 수 제한이 있습니다. 배치 처리와 적절한 지연을 구현하세요.
- **인증 오류**: JSON 키 파일이 프로젝트 디렉토리에 올바르게 저장되었는지 확인하세요.