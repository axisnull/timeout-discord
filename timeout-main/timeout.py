import discord
from discord.ext import commands, tasks
from datetime import datetime, timezone, timedelta
import requests
from word_detection import word_detection   #비속어 필터링

a = word_detection()
a.load_data()
a.load_badword_data()

#비속어 필터링 함수
def filter(message):
        word = str(message)
        a.input = word
        a.text_modification()
        similarity = 0.8

        a.lime_compare(a.token_badwords, a.token_detach_text[0], similarity)   #기존 비속어 비교(유사도 0.8)
        result = a.result

        a.lime_compare(a.new_token_badwords, a.token_detach_text[1], similarity, True) #초성 비속어 비교(유사도 0.8)
        result += a.result
        #비속어 없음 -> False, 비속어 감지 -> True
        if len(result) == 0:
            return False
        else:
            return True


intents = discord.Intents().all()   #디스코드의 모든 이벤트 수신
bot = commands.Bot(command_prefix=['$', ], intents=intents) #봇 생성

MSG_TO_TIMEOUT = {}


"""
디코 서버에서 특정 유저를 채팅 금지 시키는 함수
bot: 봇 객체
user_id: 대상 유저
guild_id: 서버 id
expiration: 제한 시간
"""
def timeout_user(bot, user_id, guild_id, expiration):
    url = "https://discord.com/api/v9/" + f'guilds/{guild_id}/members/{user_id}'    #특정 서버의 특정 멤버 정보
    headers = {"Authorization": f"Bot {bot.http.token}"}
    #제한 시간을 ISO 형식 문자열로 변환
    if expiration != None:
        until = expiration.isoformat()

    json = {'communication_disabled_until': until}  #채팅 금지 제한 시간 설정
    session = requests.patch(url, json=json, headers=headers)

    return session.status_code  #상태코드 200이면 성공


class Timeout:
    def __init__(self, bot, message, **kwargs):
        self.bot = bot  #디코 봇 객체

        self.activated = True   #타임아웃 활성 플래그

        self.message = message  #메세지 저장
        self.feedback_message = None    #타임아웃 메세지 저장

        self.target_users = message.author  #타임아웃 대상 유저
        self.channel = message.channel      #메세지 작성 채널
        self.guild = message.guild          #메세지 작성 서버

        self.expire_at = datetime.now(timezone.utc) + timedelta(seconds=60) #타임아웃 만료 시간(30초)


    #타임아웃 활성화 기능
    async def execute_timeout(self):
        self.activated = False  #타임아웃 실행 상태

        if self.target_users != self.bot.user:
            until = self.expire_at  #타임아웃 활성 시간
            await self.target_users.timeout(until)  #타임아웃 적용
            #채널에 타임아웃 메세지 전송
            self.feedback_message = await self.channel.send(f"{self.target_users.mention}에게 비속어 사용으로 인한 타임아웃을 적용합니다.")

    #타임아웃 만료 기능
    async def expire(self):
        #현재 시간이 타임아웃 만료 시간보다 큰지 확인
        if datetime.now(timezone.utc) > self.expire_at:
            users = self.target_users
            if self.feedback_message:
                #채널에 타임아웃 만료 메세지 전송
                await self.channel.send(f"{users.mention}에게 적용된 타임아웃을 해제합니다")
            return True         #타임아웃 만료 상태

        else:
            return False        #시간이 남았음(타임아웃 실행 상태)


#봇이 서버에 접속할 때 발생하는 이벤트
@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))
    pool.start()


#서버에 새로운 메세지가 생성될 때 발생하는 이벤트
@bot.event
async def on_message(message):
    print("Received message:", message.content)  #확인용
    #메세지 작성자가 봇이면 x
    if message.author.bot:
        return None
    #비속어 필터 적용
    if filter(message.content) == True:
        print("비속어 감지")    #필터 확인용
        
        to = Timeout(bot, message)      #타임아웃 객체 생성
        MSG_TO_TIMEOUT[message] = to    #메세지+타임아웃 객체 저장
        await to.execute_timeout()      #타임아웃 실행


@tasks.loop(seconds=10)
async def pool():
    expired = []
    
    #현재 모든 타임아웃 확인
    for msg in MSG_TO_TIMEOUT:
        to = MSG_TO_TIMEOUT[msg]
        #타임아웃 만료 여부 확인
        if await to.expire():
            expired.append(msg)
    #타임아웃 만료된 메세지 제거
    for msg in expired:
        MSG_TO_TIMEOUT.pop(msg)


if __name__ == '__main__':
    with open('token.txt') as f:    #디코 봇 토큰
        TOKEN = f.read()


    bot.run(TOKEN)  #디코 봇 실행