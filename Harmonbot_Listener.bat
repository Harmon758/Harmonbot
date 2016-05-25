if not exist bin mkdir bin
cd bin
:loop
go install Harmonbot_Listener
Harmonbot_Listener.exe
goto loop
PAUSE