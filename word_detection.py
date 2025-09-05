#coding:utf-8

import pickle
from typing import List

korean_one = ['ㄱ','ㄲ','ㄴ','ㄷ','ㄸ','ㄹ','ㅁ','ㅂ','ㅃ','ㅅ',
              'ㅆ','ㅇ','ㅈ','ㅉ','ㅊ','ㅋ','ㅌ','ㅍ','ㅎ']
korean_two = ['ㅏ','ㅐ','ㅑ','ㅒ','ㅓ','ㅔ','ㅕ','ㅖ','ㅗ','ㅘ',
              'ㅙ','ㅚ','ㅛ','ㅜ','ㅝ','ㅞ','ㅟ','ㅠ','ㅡ','ㅢ','ㅣ']
korean_three = ['','ㄱ','ㄲ','ㄳ','ㄴ','ㄵ','ㄶ','ㄷ','ㄹ','ㄺ',
                'ㄻ','ㄼ','ㄽ','ㄾ','ㄿ','ㅀ','ㅁ','ㅂ','ㅄ','ㅅ',
                'ㅆ','ㅇ','ㅈ','ㅊ','ㅋ','ㅌ','ㅍ','ㅎ']

"""
askicode // 588 -> 초성 인덱스
(askicode // 28) % 21 -> 중성 인덱스
askicode % 28 -> 종성 인덱스
"""

#한글 음절을 초성, 중성, 종성으로 분리하여 토큰화하는 함수
def detach_word(word : List,before : List) -> List:
    result = []
    askicode = ord(word[0]) - 44032     #'가'(유니코드: 44032) 기준으로 인덱스 구하기
    #음절이 가~힣 사이에 있을 때
    if -1 < askicode and askicode < 11173:
        #초성이 ㅇ일 때(불필요한 초성 토큰 제외)
        if askicode // 588 == 11:
            if len(before) > 0 and before[-1][0] in korean_two and before[-1][0]==korean_two[(askicode // 28) % 21]:
                pass
            elif len(before) > 1 and before[-2][0] in korean_two and before[-2][0]==korean_two[(askicode // 28) % 21]:
                pass
            else:
                result.append([korean_one[askicode // 588],word[1]])
                result.append([korean_two[(askicode // 28) % 21],word[1]])
        #초성, 중성 분리
        else:
            result.append([korean_one[askicode // 588],word[1]])
            result.append([korean_two[(askicode // 28) % 21],word[1]])
        #종성 처리
        if korean_three[askicode % 28] == '':
            pass
        else:
            result.append([korean_three[askicode % 28],word[1]])
    #한글이 아닐 때
    else:
        result.append(word)
    return result

#글자수가 짧을수록 엄격하게 적용하는 가중치 함수
def make_better(x : int) -> int:
    return 0.1**((x-3)/10)+1.3          #가중치 리턴


class word_detection():

    def __init__(self) -> None:
        self.base_layer = {}            #기본 비속어 데이터
        self.seem_layer = {}            #시각적으로 유사한 글자 대응 데이터
        self.keyboard_layer = {}        #키보드 오타 대응 데이터
        self.pronunciation_layer = {}   #발음이 유사한 글자 대응 데이터

        #입력, 처리 결과 저장 변수
        self.input = ''                 #입력 문자열
        self.token_detach_text = []     #detach_word로 토큰화, detach 완료된 입력 문자열 리스트
        self.nontoken_badwords = []     #토큰화하지 않은 비속어 리스트
        self.token_badwords = []        #토큰화 완료된 비속어 리스트
        self.result = []                #결과 값
        self.new_nontoken_badwords = [] # 토큰화하지 않은 초성 리스트
        self.new_token_badwords = []    # 토큰화 완료된 초성 리스트


    def load_data(self) -> None:
        #WDLD.txt로부터 읽어온 데이터 로드
        with open('WDLD.txt', 'rb') as f:
            self.base_layer = pickle.load(f)
            self.seem_layer = pickle.load(f)
            self.keyboard_layer = pickle.load(f)
            self.pronunciation_layer = pickle.load(f)
        return None


    #Badwords.txt 파일에서 읽어온 비속어 데이터 저장 함수
    def load_badword_data(self,file : str ="Badwords.txt") -> None:
        f=open(file,'r',encoding="utf-8")
        while True:
            line = f.readline()
            if not line:
                break
            self.add_badwords(line[0:-1])   #개행 문자 제거 후 비속어 추가
        f.close()
        
        self.tokenize_badwords()            #비속어 데이터 토큰화
        return None


    #비속어를 입력받아 비속어 리스트에 추가 함수
    def add_badwords(self , badword : str) -> None:
        #nontoken_badwords에 있으면 추가x
        if badword in self.nontoken_badwords:
            return None
        #'#'으로 시작되는 라인 추가x(주석)
        elif badword.startswith('#'):
            return None
        #초성 new_nontoken_badwords에 추가
        elif badword.startswith('$'):
            if badword[1:] not in self.new_nontoken_badwords:
                self.new_nontoken_badwords.append(badword[1:])
            return None
        #그 외 비속어 nontoken_badwords에 추가
        else:
            if badword not in self.nontoken_badwords:
                self.nontoken_badwords.append(badword)
        return None


    # 비속어 토큰화 함수
    def tokenize_badwords(self) -> None:
        #기존 비속어(nontoken_badwords) 토큰화
        result = []
        for i in self.nontoken_badwords:
            iList = []
            for j in range(0,len(i)):
                Dj = detach_word([i[j],j],iList)
                for k in range(0,len(Dj)):
                    if Dj[k][0] in self.base_layer:
                        Dj[k][0] = self.base_layer[Dj[k][0]]
                        iList.append(Dj[k])
            result.append(iList)
        self.token_badwords = result
        result = []

        #추가된 비속어(new_nontoken_badwords) 토큰화
        for i in self.new_nontoken_badwords:
            ilist = []
            for j in range(0,len(i)):
                ilist.append([self.base_layer[i[j]],j])
            result.append(ilist)
        self.new_token_badwords = result


    #self.input 문자열 처리 -> self.token_detach_text에 저장(입력 데이터 토큰화)
    def text_modification(self) -> None:
        PassList = [' ']
        result = []
        word = self.input

        #연속된 중복 문자 제거 후 저장
        for i in range(len(word)):
            if word[i] not in PassList:
                if i == len(word)-1:
                    result.append([self.input[i],i])
                else:
                    if word[i] == word[i+1][0]:
                        pass
                    else:
                        result.append([self.input[i],i])
            else:
                pass
        
        #detach_word 함수로 초성, 중성, 종성 분리
        result1 = []
        new_layer=[]  #초성 번호
        for i in range(0,len(result)):
            de = detach_word(result[i],result1)
            #단일 글자 and 초성만 있는 경우
            if len(de)==1 and de[0][0] not in korean_two:
                new_layer.append(len(result1))
            for j in de:
                result1.append(j)
        result = result1

        #대응 데이터 적용(시각적 유사 글자, 키보드 오타, 발음 유사)
        result1 = [[],[],[],[]]     #[시각적 유사 글자, 키보드 오타, 발음 유사, 기본]
        new_re = [[],[],[]]         #새로운 초성

        for j in range(0,len(result)):
            i = result[j]

            if i[0] in self.seem_layer or i[0] in self.keyboard_layer or i[0] in self.pronunciation_layer:
                #시각적 유사 글자(예시: ㄱ/ㄲ, ㅈ/ㅊ)
                if i[0] in self.seem_layer:
                    result1[0].append((self.seem_layer[i[0]],i[1]))             #(대체 글자, 원래 위치)
                    #초성만 있는 토큰
                    if j in new_layer:
                        new_re[0].append((self.seem_layer[i[0]],i[1]))
                #시각적 유사 글자x -> 발음 유사 데이터
                else:
                    if i[0] in self.pronunciation_layer:
                        result1[0].append((self.pronunciation_layer[i[0]],i[1]))

                #키보드 오타(예시: ㄱ/ㅅ, ㅈ/ㅂ)
                if i[0] in self.keyboard_layer:
                    result1[1].append((self.keyboard_layer[i[0]],i[1]))         #(대체 글자, 원래 위치)
                    #초성만 있는 토큰
                    if j in new_layer:
                        new_re[1].append((self.keyboard_layer[i[0]],i[1]))
                #키보드 오타x -> 시각적 유사 글자
                else:
                    if i[0] in self.seem_layer:
                        result1[1].append((self.seem_layer[i[0]],i[1]))
                        if j in new_layer:
                            new_re[0].append((self.seem_layer[i[0]],i[1]))

                #발음 유사(예시: ㅂ/ㅍ, ㅔ/ㅐ)
                if i[0] in self.pronunciation_layer:
                    result1[2].append((self.pronunciation_layer[i[0]],i[1]))    #(대체 글자, 원래 위치)
                #발음 유사x -> 시각적 유사 글자
                else:
                    if i[0] in self.seem_layer:
                        result1[2].append((self.seem_layer[i[0]],i[1]))

            #기본 글자 적용
            if i[0] in self.base_layer:
                result1[0].append((self.base_layer[i[0]],i[1])) #시각적 유사(원래 글자, 원래 위치)
                result1[2].append((self.base_layer[i[0]],i[1])) #발음 유사(원래 글자, 원래 위치)
                result1[3].append((self.base_layer[i[0]],i[1])) #기본(원래 글자, 원래 위치)
                #초성만 있는 토큰
                if j in new_layer:
                    new_re[0].append((self.base_layer[i[0]],i[1]))
                    new_re[1].append((self.base_layer[i[0]],i[1]))
                    new_re[2].append((self.base_layer[i[0]],i[1]))
            else:
                pass

        result = result1
        self.token_detach_text = [result, new_re]    #토큰화 결과 저장(모든 유사 글자 비교, 초성 토큰)
        return None


    """
    입력 데이터(check_text)와 비속어 토큰(compare_badword)사이 유사도 계산
    반환값: 0~1 사이, 숫자가 높을수록 유사
    """
    def word_comparing(self , check_text : List, compare_badword : List) -> int:
        a = 0
        for i in range(len(check_text)):
            j = None
            for k in range(0,len(check_text)):
                #입력 데이터의 i번째 토큰과 비속어 k번째 토큰의 앞 두 자리 비교(초성+중성)
                if str(check_text[i][0])[0:2] == str(compare_badword[k][0])[0:2]:
                    if j is None:
                        j = k
                    #i에 더 가까운 k(더 작은 절대값) 선택
                    elif abs(j-i) > abs(k-i):
                        j = k
                    else:
                        pass
            #입력 데이터 i에 대응하는 비속어 토큰 j가 존재할 때
            if j is not None:
                distance = abs(j-i) #입력 데이터와 비속어 토큰 위치 차이
                weight = 0.1/(2**distance)  #가중치 계산(거리가 멀수록 낮음)
                
                check_c = int(str(check_text[i][0])[2]) #입력 데이터 i의 종성
                compare_c = int(str(compare_badword[j][0])[2])  #비속어 토큰 j의 종성
                consonant_diff = abs(check_c - compare_c)   #두 글자의 종성 차이 계산
                consonant_weight = 10 - consonant_diff
                
                score = weight * consonant_weight   #최종 점수
                a += score  #누적 점수
                
        same = a / len(compare_badword) #평균 유사도
        better = make_better(len(compare_badword))  #글자수 보정(짧을수록 엄격한 가중치)
        return same ** better   #최종 유사도


    """
    입력 데이터(check_text)와 비속어(badwords)를 비교하여 비속어인 부분과 그 확률을 리턴
    cut_line: 확률이 몇 프로 이상이면 욕설로 인식하는지 기준(0~1)
    new: 초성 검사 모드 여부
    """
    def lime_compare(self, badwords : List, check_text : List, cut_line : int = 0.9 , new : bool = False) -> List:

        b = []  #비속어 매칭 조건을 만족하는 결과
        c = {}    #점수와 매칭 정보 저장(중복 방지)
        
        for cw in check_text:
            #모든 비속어 목록 반복
            for i in range(0,len(badwords)):
                badi = badwords[i]
                for j in range(len(cw)-len(badi)+1):
                    a = self.word_comparing(cw[j:(j+len(badi))],badi)   #유사도 점수 a 계산
                    comparewordstart = cw[j]
                    comparewordend = cw[(j+len(badi))-1]
                    """
                    new=True -> 초성 비속어 토큰
                    new=False -> 그외 비속어 토큰
                    """
                    if new:
                        in_list = (comparewordstart[1],comparewordend[1],a,self.new_nontoken_badwords[i])
                    else:
                        in_list = (comparewordstart[1],comparewordend[1],a,self.nontoken_badwords[i])
                    #유사도가 cut_line 이상 and 시작 인덱스가 기록x일 때
                    if a>=cut_line and comparewordstart[1] not in c:
                        c[comparewordstart[1]] = (a,in_list)
                        b.append(in_list)
                    #시작 인덱스가 기록 but 유사도가 더 높은 경우 -> 교체
                    elif comparewordstart[1] in c and c[comparewordstart[1]][0] < a:
                        b.remove(c[comparewordstart[1]][1])
                        b.append(in_list)
                        c[comparewordstart[1]] = (a,in_list)
        self.result = b #최종 결과
        return b

if __name__ =='__main__':
    import time
    a = word_detection()
    a.load_data()
    a.load_badword_data()
    cutline = int(input("몇 %이상인 것만 출력할까요?"))
    EXECUTION = 3
    while EXECUTION!=0:
        a.input=input('필터링할 문장 입력!!')
        stime = time.time()
        a.text_modification()
        a.lime_compare(a.token_badwords , a.token_detach_text[0] , cutline/100,False)
        result = a.result
        a.lime_compare(a.new_token_badwords, a.token_detach_text[1], cutline/100,True)
        result += a.result
        print(f'{cutline}%이상 일치하는 부분만 출력\n')
        word = a.input
        if len(result)==0:
            print(' > 감지된 욕설이 없습니다 <')
        for j in result:
            word = word[:j[0]]+'*'*(j[1]-j[0]+1)+word[j[1]+1:]
            print(f' > {a.input[j[0]:j[1]+1]} < [{j[0]}~{j[1]}] :  ("{j[3]}"일 확률 {round(j[2]*100)}%)')
        print('\n소요시간 : ',time.time()-stime,'초')
        print('필터링된 문장 : ',word)
        print("\n ==================== \n")
        EXECUTION-=1
