package main

import (
	"github.com/bwmarrin/dgvoice"
	"github.com/bwmarrin/discordgo"
	
	"bufio"
	"bytes"
	"encoding/base64"
	"encoding/binary"
	"io/ioutil"
	"fmt"
	"os"
	"strings"
	"time"
	
	"keys"
)

var (
	_continue	bool
	_listen 	bool
	dgv 		*discordgo.VoiceConnection
	recv 		chan *discordgo.Packet
	send 		chan []int16
	me			*discordgo.User
)

func check(e error) {
    if e != nil {
        panic(e)
    }
}

func main() {
	fmt.Println("Starting up Harmonbot Listener...")

	// Connect to Discord
	dg, err := discordgo.New(keys.Listener_token)
	check(err)
	
	// Register ready as a callback for the ready events.
	dg.AddHandler(ready)
	// Register messageCreate as a callback for the messageCreate events.
	dg.AddHandler(messageCreate)

	// Open Websocket
	err = dg.Open()
	check(err)
	
	me, err = dg.User("@me")
	check(err)
	
	fmt.Printf("Started up %s#%s (%s)\n", me.Username, me.Discriminator, me.ID)

	_continue = true
	for _continue {
		time.Sleep(1)
	}
	
	fmt.Println("Shutting down Harmonbot Listener...")
	
	// Close connections
	if dgv != nil {
		dgv.Close()
	}
	dg.Logout()
	dg.Close()

	return
}

func ready(s *discordgo.Session, event *discordgo.Ready) {
	s.UpdateStreamingStatus(0, "with Harmonbot", "https://www.twitch.tv/discordapp")
}

func messageCreate(s *discordgo.Session, m *discordgo.MessageCreate) {
	switch m.Content {
		case "!testlistener":
			s.ChannelMessageSend(m.ChannelID, "Hello, World!")
		case ">listen":
			_listen = true
			s.ChannelMessageSend(m.ChannelID, "I'm listening..")
			Listen(dgv)
		case ">stopl":
			_listen = false
			s.ChannelMessageSend(m.ChannelID, "I stopped listening.")
		case "!restartlistener":
			if m.Author.ID == keys.Myid {
				s.ChannelMessageSend(m.ChannelID, "Restarting...")
				_continue = false
			}
		case "!listener_updateavatar":
			if m.Author.ID == keys.Myid {
				changeAvatar(s)
				s.ChannelMessageSend(m.ChannelID, "Avatar Updated.")
			}
	}
	if strings.HasPrefix(m.Content, ">join") {
		channel, err := s.Channel(m.ChannelID)
		check(err)
		_dgv, err := s.ChannelVoiceJoin(channel.GuildID, strings.Split(m.Content, " ")[1], false, false)
		check(err)
		
		_recv := make(chan *discordgo.Packet, 2)
		go dgvoice.ReceivePCM(_dgv, _recv)
		_send := make(chan []int16, 2)
		go dgvoice.SendPCM(_dgv, _send)
		
		dgv = _dgv
		recv = _recv
		send = _send
	}
}

func Listen(v *discordgo.VoiceConnection) {
	// fmt.Println("Echoing")
	
	fo, err := os.Create("../data/testing.pcm")
	check(err)

	v.Speaking(true)
	defer v.Speaking(false)
	
	w := bufio.NewWriter(fo)
	buf := new(bytes.Buffer)

	for _listen {
		p, ok := <-recv
		if !ok {
			return
		}

		send <- p.PCM
		err := binary.Write(buf, binary.LittleEndian, p.PCM)
		check(err)
	}
	
	_, err = w.Write(buf.Bytes())
	check(err)
	
	err = w.Flush()
	check(err)
	
	fo.Sync()
	
	// fmt.Println("Stopping")
}

// Helper function to change the avatar
func changeAvatar(s *discordgo.Session) {
	img, err := ioutil.ReadFile("../data/discord_harmonbot_listener_icon.png")
	check(err)

	base64 := base64.StdEncoding.EncodeToString(img)

	avatar := fmt.Sprintf("data:image/png;base64,%s", string(base64))

	_, err = s.UserUpdate("", "", me.Username, avatar, "")
	check(err)
}
