# Uniformity Marking 부적합 탐지 시스템

## 파일 구조
- Camera/ : 카메라 조작, 연결 파일
- Camera/HuarayCam.py : 카메라 조작 함수
- Camera/run_cam.py : 카메라 객체 생성, 모듈화. UI와 연결
---
- data_proc.py : MES로부터 받아온 데이터 정리
- img_proc.py : 이미지 저장 함수, 경로
- nmp.py : MES와 소켓 통신 모듈화
- run.py : Worker - NMP - Camera 연결
- ui.py : UI 시각화
- worker.py : 객체 탐지, 부적합 판정 알고리즘 실제 수행
- main.py : Thread 생성, ui와 runner Thread 분리해 실행
