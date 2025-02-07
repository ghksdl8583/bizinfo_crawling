import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager  # 자동 드라이버 매니저 사용
from datetime import datetime, timedelta
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Chrome 옵션 설정
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# ChromeDriver 설정
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

# 날짜 설정 (오늘과 어제)
today = datetime.now().strftime("%Y-%m-%d")
yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

def fetch_bizinfo(url):
    driver.get(url)
    print("페이지 로드 중...")

    # 테이블 로드 대기
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody"))
    )
    print("테이블 로드 완료.")

    projects = []
    rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")

    for row in rows:
        cells = row.find_elements(By.TAG_NAME, "td")
        
        if len(cells) >= 7:
            지원분야 = cells[1].text.strip()
            지원사업명 = cells[2].text.strip()
            지원사업명_링크 = cells[2].find_element(By.TAG_NAME, "a").get_attribute("href")
            신청기간 = cells[3].text.strip()
            소관부처 = cells[4].text.strip()
            사업수행기관 = cells[5].text.strip()
            등록일 = cells[6].text.strip()

            # 등록일이 오늘 또는 어제인 경우 저장
            if 등록일 in [today, yesterday]:
                projects.append({
                    "지원분야": 지원분야,
                    "지원사업명": 지원사업명,
                    "신청기간": 신청기간,
                    "소관부처": 소관부처,
                    "사업수행기관": 사업수행기관,
                    "등록일": 등록일,
                    "링크": 지원사업명_링크
                })

    return projects

# HTML 테이블 생성 함수 (동일)
def create_html_table(projects, region_name):
    if not projects:
        return f"<h3>{region_name} 공고: 없음</h3>"

    table_html = f"<h3>{region_name} 지원사업 공고</h3><table border='1' style='border-collapse: collapse; width: 100%;'>"
    table_html += "<tr><th>지원분야</th><th>지원사업명</th><th>신청기간</th><th>소관부처</th><th>사업수행기관</th><th>등록일</th><th>링크</th></tr>"

    for project in projects:
        table_html += f"""
            <tr>
                <td>{project['지원분야']}</td>
                <td>{project['지원사업명']}</td>
                <td>{project['신청기간']}</td>
                <td>{project['소관부처']}</td>
                <td>{project['사업수행기관']}</td>
                <td>{project['등록일']}</td>
                <td><a href="{project['링크']}">링크</a></td>
            </tr>
        """
    table_html += "</table><br>"
    return table_html

# 메일 보내기 함수 (동일)
def send_email(jeonnam_html, central_gov_html, recipient_email):
    sender_email = "ghksdl8583@gmail.com"  # 본인 이메일 주소 입력
    sender_password = "eepf eajb rgot oyen"  # 앱 비밀번호 설정 필요 (Gmail 기준)

    msg = MIMEMultipart("alternative")
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg["Subject"] = "지원사업 공고 알림 - 전남 & 중앙부처"

    # 이메일 본문
    body = f"""
    <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                }}
                table {{
                    border-collapse: collapse;
                    width: 100%;
                }}
                th, td {{
                    border: 1px solid #ddd;
                    padding: 8px;
                    text-align: left;
                }}
                th {{
                    background-color: #f2f2f2;
                }}
            </style>
        </head>
        <body>
            <h2>새로운 지원사업 공고 알림</h2>
            {jeonnam_html}
            {central_gov_html}
        </body>
    </html>
    """

    msg.attach(MIMEText(body, "html"))

    # SMTP 서버 연결 및 메일 전송
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        print(f"메일 전송 성공: {recipient_email}")
    except Exception as e:
        print(f"메일 전송 실패: {e}")

if __name__ == "__main__":
    # 전남 지역 공고 URL
    jeonnam_url = "https://www.bizinfo.go.kr/web/lay1/bbs/S1T122C128/AS/74/list.do?hashCode=&rowsSel=6&rows=15&cpage=1&cat=&article_seq=&pblancId=&schJrsdCodeTy=&schWntyAt=&schAreaDetailCodes=6460000&schEndAt=N&orderGb=&sort=&condition=searchPblancNm&condition1=AND&preKeywords=&keyword="
    
    # 중앙부처 공고 URL
    central_gov_url = "https://www.bizinfo.go.kr/web/lay1/bbs/S1T122C128/AS/74/list.do?hashCode=&rowsSel=6&rows=15&cpage=1&cat=&article_seq=&pblancId=&schJrsdCodeTy=2&schWntyAt=&schAreaDetailCodes=&schEndAt=N&orderGb=&sort=&condition=searchPblancNm&condition1=AND&preKeywords=&keyword="
    
    # 전남 지역과 중앙부처 공고 크롤링
    jeonnam_projects = fetch_bizinfo(jeonnam_url)
    central_projects = fetch_bizinfo(central_gov_url)

    # HTML 테이블 생성
    jeonnam_html = create_html_table(jeonnam_projects, "전남 지역")
    central_gov_html = create_html_table(central_projects, "중앙부처")

    # 메일 발송 설정 (받는 사람의 이메일 입력)
    recipient_email = "swi3301@seowooin.com"
    send_email(jeonnam_html, central_gov_html, recipient_email)

    driver.quit()
