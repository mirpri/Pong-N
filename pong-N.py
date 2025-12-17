from tkinter import *
from tkinter.ttk import*
import keyboard
import _thread
import time
import random
from subprocess import run
import sv_ttk
import ctypes
import os
import importlib.util
import json

from default_controls import *

MAX_POINTS = 5
AUTO_SERVE = False
NO_WAIT = False

ctypes.windll.shcore.SetProcessDpiAwareness(2)

root = Tk()
root.title('Pong Neon')
root.geometry('700x950')
#root.option_add('*background','#002255')
#root.option_add('*foreground','ivory')
#root.config(background='#002255')

sv_ttk.set_theme("light")

p_name=['balanced','large','friction','swift','Sparky','Lightning','Archer' ,'Smokey',     'Wizard'    ,     '(test)','<random>']
p_width=[40,          55,      30,       27,     30,        35    ,   38    ,   30   ,        34        ,      1000,      30]
p_fric=[100,         100,      40,       200,    100,      300    ,   110   ,   120  ,         90       ,       100,       100]
p_speed=[14,          10,       12,      18,     12,        12    ,   13    ,   12   ,        11      ,         0,         0]
p_color=['gray','tan','darkseagreen','blueviolet','peru','skyblue' ,'orchid', 'rosybrown',  'crimson' ,  'whitesmoke','white']
p_ac=[    0,          0,        0,      0,        0.4,      0.5,      1 ,      0.7  ,         0.8 ,              0,       0]
p_ex=[   200,         200,      200,     200,     100,       80,       70,     90    ,        100 ,             200,     200]
p_cnr=[     1.4,      1.2,      0.9,     1.5,     1.2,       1.2    ,    1   ,  1.1,          0.9 ,              1,      1]


controls=['WASD','arrows']
dire_ctrl_func=[asd,arrow]
skil_ctrl_func=[asd_s,arrow_s]
controls_dir = './controls'

def load_controls():
    for file in os.listdir(controls_dir):
        if file.endswith('.py'):
            try:
                control_name = file[:-3]
                file_path = os.path.join(controls_dir, file)
                spec = importlib.util.spec_from_file_location(control_name, file_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                controls.append(control_name)
                dire_ctrl_func.append(getattr(module, 'control'))
                skil_ctrl_func.append(getattr(module, 'control_s'))
            except:
                pass

try:
    load_controls()
except:
    pass
print(controls, dire_ctrl_func)

def Sparky_app(x):
    global p1ready,p2ready
    if x==1:
        p1ready=1
        M.itemconfig(p1p,fill='aqua')
    elif x==2:
        p2ready=1
        M.itemconfig(p2p,fill='aqua')
def Sparky_hit(x):
    global vy,p1ready,p2ready
    if x==1:
        p1ready=0
        M.itemconfig(p1p,fill='peru')
    elif x==2:
        p2ready=0
        M.itemconfig(p2p,fill='peru')
    vy*=20
def lightning(x):
    global p1stop,p2stop,p1ready,p2ready,p1e,p2e
    for i in range(2):
        for j in M.find_all():
            M.move(j,2,2)
        time.sleep(1/10)
        for j in M.find_all():
            M.move(j,-2,-2)
        time.sleep(1/10)
    if x==1:
        p2stop+=1
        p2e=max(p2e-25,0)
        p1ready=1
        for i in range(3):
            M.move(p2p,0,10)
            time.sleep(1/25)            
            M.move(p2p,0,-10)
            time.sleep(1/25)
        p1ready=0
        p2stop-=1
    elif x==2:        
        p1stop+=1
        p1e=max(p1e-25,0)
        p2ready=1
        for i in range(3):
            M.move(p1p,0,10)
            time.sleep(1/25)            
            M.move(p1p,0,-10)
            time.sleep(1/25)
        p2ready=0        
        p1stop-=1
def Lightning_app(x):
    _thread.start_new_thread(lightning,(x,))
def Lightning_hit(x):
    pass
def Archer_app(x):
    _thread.start_new_thread(aiming,(x,))
def aiming(x):
    global p1ready,p2ready,p1stop,p2stop,p1a,p2a
    aim=M.create_text(300,400,text='+',font='Arial 30',fill='orchid')    
    if x==1:
        p1a=300
        p1ready=1        
        p1stop+=1
        while gaming and p1ready:
            if keyboard.is_pressed('a') and not keyboard.is_pressed('d') and p1a>0:
                p1a-=30
                M.move(aim,-30,0)
            elif keyboard.is_pressed('d') and not keyboard.is_pressed('a') and p1a<600:
                p1a+=30
                M.move(aim,30,0)
            if keyboard.is_pressed('w'):
                p1ready=0
                break
            time.sleep(1/25)        
        p1stop-=1
    elif x==2:
        p2a=300
        p2ready=1        
        p2stop+=1
        while gaming and p2ready:
            if keyboard.is_pressed('4') and not keyboard.is_pressed('6') and p2a>0:
                p2a-=30
                M.move(aim,-30,0)
            elif keyboard.is_pressed('6') and not keyboard.is_pressed('4') and p2a<600:
                p2a+=30
                M.move(aim,30,0)
            if keyboard.is_pressed('8'):
                p2ready=0
                break
            time.sleep(1/25)        
        p2stop-=1
    M.delete(aim)
def Archer_hit(i):
    global p1ready,p2ready,vx,vy,p1a,p2a,x,y
    if i==1:
        p1ready=0        
        vx,vy=(p1a-x)/((p1a-x)**2+(400-y)**2)**0.5*20,(400-y)/((p1a-x)**2+(400-y)**2)**0.5*max(15,(vx**2+vy**2)**0.5)
    if i==2:
        p2ready=0        
        vx,vy=(p2a-x)/((p2a-x)**2+(400-y)**2)**0.5*20,(400-y)/((p2a-x)**2+(400-y)**2)**0.5*max(15,(vx**2+vy**2)**0.5)

def stamplif(x,y,sz,colorlight='#eeeedd',colordark='gray'):
    if not dark:
        s=M.create_oval(x-10*sz,y-10*sz,x+10*sz,y+10*sz,width=0,fill=colorlight)
    if dark:
        s=M.create_oval(x-10*sz,y-10*sz,x+10*sz,y+10*sz,width=0,fill=colordark)
    M.lift(s)
    for i in range(10):
        M.coords(s,x-(10-i)*sz,y-(10-i)*sz,x+(10-i)*sz,y+(10-i)*sz)
        time.sleep(0.1)
    M.delete(s)
def smoke(ii):
    global x,y,p1ready,p2ready
    if ii==1:
        p1ready=1
    elif ii==2:
        p2ready=1
    for i in range (5):
        _thread.start_new_thread(stamplif,(x,y,3*i))
        time.sleep(0.2)
    if ii==1:
        p1ready=0
    elif ii==2:
        p2ready=0
def Smokey_app(i):
    _thread.start_new_thread(smoke,(i,))
def Smokey_hit(i):
    global x,y
    _thread.start_new_thread(stamplif,(x,y,random.randint(35,50)))
def Wizard_app(i):
    global a,x,y
    _thread.start_new_thread(stamplif,(x,y,2,'crimson','crimson'))
    a=0.1*(random.randint(0,1)-0.5)*vy


#p_effe=['']
p1t=p2t=0
p1c=0
p2c=1
def drawpad():    
    M.coords(p1p,(p1-p_width[p1t],700,p1+p_width[p1t],710))
    M.coords(p2p,(p2-p_width[p2t],90,p2+p_width[p2t],100))
    M.itemconfig(p1p,fill=p_color[p1t])
    M.itemconfig(p2p,fill=p_color[p2t])

def todrawpad(x):
    global p1t,p2t
    c1=C1.get()
    c2=C2.get()
    
    p1t=p_name.index(c1)
    p2t=p_name.index(c2)

    drawpad()
    if C1.get()=='Archer':
        C11.set('WASD')
        setcontrol(0)
    if C2.get()=='Archer':
        C22.set('arrows')
        setcontrol(0)

def setcontrol(x):
    global p1c,p2c
    if C1.get()=='Archer':
        C11.set('WASD')
    if C2.get()=='Archer':
        C22.set('arrows')
    p1c=controls.index(C11.get())
    p2c=controls.index(C22.get())

F1=Frame(root)
L1=Label(F1,text='  |  '+'⚪'*5)
C1=Combobox(F1,values=p_name,width=8)
C1.set(p_name[0])
C1.bind("<<ComboboxSelected>>",todrawpad)

C11=Combobox(F1,values=controls,width=8)
C11.set('WASD')
C11.bind("<<ComboboxSelected>>",setcontrol)

P1=Progressbar(root,mode='determinate',length=500)

C11.pack(side='left')
C1.pack(side='left')
L1.pack(side='left')
F2=Frame(root)
L2=Label(F2,text='  |  '+'⚪'*5)

C2=Combobox(F2,values=p_name,width=8)
C2.set(p_name[0])
C2.bind("<<ComboboxSelected>>",todrawpad)

C22=Combobox(F2,values=controls,width=8)
C22.set('arrows')
C22.bind("<<ComboboxSelected>>",setcontrol)

P2=Progressbar(root,mode='determinate',length=500)

C22.pack(side='left')
C2.pack(side='left')
L2.pack(side='left')

M=Canvas(root,height=800,width=600,bg='white')
F2.pack(expand=1)
P2.pack(expand=1)
M.pack(padx=5)
P1.pack(expand=1)
F1.pack(expand=1)

#keyboard.press_and_release('shift')

p1=300
p2=300
p1p=M.create_rectangle(0,0,0,0)
p2p=M.create_rectangle(0,0,0,0)
ball=M.create_oval(300-10,400-10,300+10,400+10,fill='red',outline='orange',width=0)
drawpad()

gaming=0
LOGSTATE=0
LOGDATA=[]

def match(ii=5,allrandom=0):
    global gaming
    gaming=1    
    s1=s2=0
    if ii<10:
        L1.config(text='  |  '+'⚫'*s1+'⚪'*(ii-s1))
        L2.config(text='  |  '+'⚫'*s2+'⚪'*(ii-s2))
    else:
        L1.config(text=f'  |  {s1} / {ii}')
        L2.config(text=f'  |  {s2} / {ii}')
    c1=C1.get()
    c2=C2.get()
    if c1=='<random>':
        c1=p_name[random.randint(0,len(p_name)-3)]
        C1.set(c1)
    if c2=='<random>':
        c2=p_name[random.randint(0,len(p_name)-3)]
        C2.set(c2)
    todrawpad(0)

    while gaming:
        if allrandom:
            c1=p_name[random.randint(0,len(p_name)-3)]
            C1.set(c1)
            c2=p_name[random.randint(0,len(p_name)-3)]
            C2.set(c2)            
            todrawpad(0)
        win=game()
        if not gaming:
            break
        if win==1:
            s1+=1        
        else:
            s2+=1
        if s1==s2 and s1==ii-1 and ii<10:
            ii+=1
        if gaming and not NO_WAIT:
            presentstar(win)
        if (ii<10):
            L1.config(text='  |  '+'⚫'*s1+'⚪'*(ii-s1))
            L2.config(text='  |  '+'⚫'*s2+'⚪'*(ii-s2))
        else:
            L1.config(text=f'  |  {s1} / {ii}')
            L2.config(text=f'  |  {s2} / {ii}')
        if s1==ii or s2==ii:
            gaming=0
    if s1==ii:
        presentstar(1,ii)
    elif s2==ii:
        presentstar(2,ii)

    F3.pack(pady=5)      
    B1.config(state=NORMAL)
    C1.config(state=NORMAL)
    C2.config(state=NORMAL)
    C11.config(state=NORMAL)
    C22.config(state=NORMAL)
    return

def stamp(x,y):
    if not dark:
        s=M.create_oval(x-10,y-10,x+10,y+10,width=0,fill='pink')
    if dark:
        s=M.create_oval(x-10,y-10,x+10,y+10,width=0,fill='brown')
    M.lower(s)
    for i in range(10):
        M.coords(s,x-(10-i),y-(10-i),x+(10-i),y+(10-i))
        time.sleep(0.1)
    M.delete(s)


def presentstar(p,num=1):
    if p==1:
        color=p_color[p1t]
    else:
        color=p_color[p2t]
    coin=M.create_text(300,400,text="✨"*num,fill=color,font='Arial 1')
    for i in range(10):
        M.itemconfig(coin,font='Arial '+str(int(i*50/(num+4))))
        time.sleep(0.03)
    for i in range(20):
        M.move(coin,0,50*(1.5-p))
        time.sleep(0.03)
    M.delete(coin)

def game():
    global x,y,vx,vy,a,p1e,p2e,p1ready,p2ready,p1v,p2v,p1stop,p2stop,p1c,p2c
    p1=300
    p2=300
    p1e,p2e,p1ready,p2ready,p1stop,p2stop=0,0,0,0,0,0
    p1v,p2v=p_speed[p1t],p_speed[p2t]
    x,y=300,400
    a=0
    tick=0
    M.coords(ball,(x-10,y-10,x+10,y+10))
    drawpad()
    vx,vy=5*(2*random.randint(0,1)-1),6*(2*random.randint(0,1)-1)
    #vx=0
    root.update()
    #keyboard.wait('space')
    while gaming:
        if AUTO_SERVE:
            break
        if keyboard.is_pressed('space'):
            break
        time.sleep(0.02)
    boring=0
    while gaming:
        s_t=time.time()
        v1,v2=0,0
        x_c,y_c=x,y
        vx+=a

        if p1e<100:
            p1e+=p_ac[p1t]
            P1['value']=int(p1e)
        if p2e<100:
            p2e+=p_ac[p2t]
            P2['value']=int(p2e)

        cc1=dire_ctrl_func[p1c]([x,y,vx,vy,a,p1,p2],1)
        cc2=dire_ctrl_func[p2c]([x,y,vx,vy,a,p1,p2],2)

        if cc1<0 and not p1stop and p1>p_width[p1t]:
            p1-=p1v
            v1-=1
            M.move(p1p,-p1v,0)
        if cc1>0 and not p1stop and p1<600-p_width[p1t]:
            p1+=p1v
            v1+=1
            M.move(p1p,p1v,0)
        if cc2<0 and not p2stop and p2>p_width[p2t]:
            p2-=p2v
            v2-=1
            M.move(p2p,-p2v,0)
        if cc2>0 and not p2stop and p2<600-p_width[p2t]:
            p2+=p2v
            v2+=1
            M.move(p2p,p2v,0)
        if p1e>=p_ex[p1t] and skil_ctrl_func[p1c]([x,y,vx,vy,a,p1,p2],1) and not p1ready:
            keyboard.release('s')
            p1e-=p_ex[p1t]
            exec(p_name[p1t]+'_app(1)')
        if p2e>=p_ex[p2t] and skil_ctrl_func[p2c]([x,y,vx,vy,a,p1,p2],2) and not p2ready:
            keyboard.release('2')
            p2e-=p_ex[p2t]
            exec(p_name[p2t]+'_app(2)')

        x,y=x+vx,y+vy
        if x<10:
            vx=-vx
            x=10
        elif x>590:
            vx=-vx
            x=590

        if min(80,110+vy)<y<110 and abs(p2-x)<p_width[p2t]+10:
            if y-vy<80 :#and abs(x-p2)>p_width[p2t]+5:
                if x>p2:
                    vx=abs(vx)
                else:
                    vx=-abs(vx)
                vy*=p_cnr[p2t]
                vx*=p_cnr[p2t]
                print('p2^')
            vy=-vy+1
            vx+=v2*p2v/4
            a=(v2*p2v-vx)/p_fric[p2t]
            y=110
            if p2ready:
                exec(p_name[p2t]+'_hit(2)')
            #print(vy)
        elif max(720,690+vy)>y>690 and abs(p1-x)<p_width[p1t]+10:
            if y-vy>690 :#and abs(x-p1)>p_width[p1t]+5:
                if x>p1:
                    vx=abs(vx)
                else:
                    vx=-abs(vx)
                vy*=p_cnr[p1t]
                vx*=p_cnr[p1t]
                print('p1^')
            vy=-vy-1
            vx+=v1*p1v/4
            a=(v1*p1v-vx)/p_fric[p1t]
            y=690            
            if p1ready:
                exec(p_name[p1t]+'_hit(1)')
            #print(vy)
        M.move(ball,x-x_c,y-y_c)
        if random.randint(0,1)==0 and not NO_WAIT:
            _thread.start_new_thread(stamp,(x,y))

        if abs(vx)<abs(0.3*vy):
            boring+=1
            if boring>250:
                M.itemconfig(ball,width=int((boring-250)/5))
                if boring>300:
                    #vx=random.randint(int(abs(vy)),int(abs(vy*2)))*(random.randint(0,1)-0.5)
                    a=0.2*(random.randint(0,1)-0.5)*vy
                    boring=0
                    M.itemconfig(ball,width=0)
            #print(boring)
        else:
            boring=0
            M.itemconfig(ball,width=0)
        if vx>40:
            vx-=0.2
        if vx<-40:
            vx+=0.2
        if vy>40:
            vy=40
            print(vy)
        elif vy<-40:
            vy=-40
            print(vy)
        elif vy>25:
            vy-=0.2
        elif vy<-25:
            vy+=0.2
        if y<0:
            time.sleep(0.1)
            p1ready=p2ready=p1stop=p2stop=0
            return 1
        elif y>800:
            time.sleep(0.1)
            p1ready=p2ready=p1stop=p2stop=0
            return 2

        #root.update()
        #print(0.02-time.time()+s_t)
        tick+=1
        if LOGSTATE and tick%2==0:
            LOGDATA.append([x,y,vx,vy,a,p1,p2,v1,v2])

        if NO_WAIT:
            continue

        sleep_t=(1/25)-time.time()+s_t
        if sleep_t>0:
            time.sleep(sleep_t)
        else:
            #print(sleep_t,'!')
            pass

started=False
def startmatch(event=0):
    global gaming,started
    if not started:       
        keyboard.press_and_release('shift')
        started=True
    if gaming:
        return
    C1.set(p_name[p1t])
    C2.set(p_name[p2t])
    C11.set(controls[p1c])
    C22.set(controls[p2c])
    F3.forget()
    B1.config(state=DISABLED)
    C1.config(state=DISABLED)
    C2.config(state=DISABLED)
    C11.config(state=DISABLED)
    C22.config(state=DISABLED)
    B1.focus_set()
    if ch1.get():
        _thread.start_new_thread(match,(3,1))
    else:
        _thread.start_new_thread(match,(MAX_POINTS,))


def togglelog():
    global LOGSTATE
    if LOGSTATE:
        LOGSTATE=0
        with open('log.txt','w') as f:
            f.write(str(LOGDATA))
        B2.config(text='Log')
    else:
        LOGSTATE=1
        B2.config(text='Loging')
dark=0
def themealt():
    global dark
    if dark:
        sv_ttk.set_theme('light')
        M.config(bg='white')
        M.itemconfig(ball,fill='red')
        dark=0
    else:
        sv_ttk.set_theme('dark')
        M.config(bg='#333333')
        M.itemconfig(ball,fill='#FF8888')
        dark=1
ch1=IntVar()
F3=Frame(root)
F3.pack(pady=5)
B1=Button(F3,text='Start',width=20,command=startmatch)
B1.pack(side='left',padx=2)
Ch1=Checkbutton(F3,text='All-Random',variable=ch1,onvalue=1,offvalue=0,width=15)
Ch1.pack(side='left',padx=2)
B2=Button(F3,text='Log',command=togglelog,width=10)
B2.pack(side='left',padx=2)
B3=Button(F3,text='🔆',command=themealt,width=3)
B3.pack(padx=2)
#keyboard.is_pressed('a')
#_thread.start_new_thread(game,())
# TODO: add model traininng mode: consecutive and background executions

def forcestop(x):
    global gaming
    gaming=0




def load_config():
    global MAX_POINTS, AUTO_SERVE, LOGSTATE, NO_WAIT
    if os.path.exists('config.json'):
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
            
            if 'p1' in config:
                if 'name' in config['p1'] and config['p1']['name'] in p_name:
                    C1.set(config['p1']['name'])
                if 'control' in config['p1'] and config['p1']['control'] in controls:
                    C11.set(config['p1']['control'])
            
            if 'p2' in config:
                if 'name' in config['p2'] and config['p2']['name'] in p_name:
                    C2.set(config['p2']['name'])
                if 'control' in config['p2'] and config['p2']['control'] in controls:
                    C22.set(config['p2']['control'])
            
            todrawpad(0)
            setcontrol(0)

            if 'max_points' in config:
                MAX_POINTS = config['max_points']
            
            if 'auto_continue' in config:
                AUTO_SERVE = config['auto_continue']
            
            if 'log' in config and config['log']:
                if not LOGSTATE:
                    togglelog()
            
            if 'no_wait' in config:
                NO_WAIT = config['no_wait']
            
            print("Config loaded")
        except Exception as e:
            print(f"Error loading config: {e}")

load_config()

root.bind('<Escape>',forcestop)
root.bind('<Return>',startmatch)
root.mainloop()

#pyinstaller -F -w pong-N.py