package main

import (
	"bufio"
	"bytes"
	"encoding/base64"
	"encoding/binary"
	"fmt"
	"io/ioutil"
	"os"
	"runtime"
	"strings"

	"github.com/bwmarrin/dgvoice"
	"github.com/bwmarrin/discordgo"
	"github.com/joho/godotenv"
)

const owner_id string = "115691005197549570"

var _continue chan bool
var _listen bool
var dgv *discordgo.VoiceConnection
var recv chan *discordgo.Packet
var send chan []int16
var me *discordgo.User
var token string

// var response		*discordgo.Message

func check(e error) {
	if e != nil {
		panic(e)
	}
}

func main() {
	fmt.Println("Starting up Discord Harmonbot Listener...")
	_continue = make(chan bool)

	// Load Credentials
	godotenv.Load("../.env")
	token = os.Getenv("DISCORD_LISTENER_BOT_TOKEN")

	// Connect to Discord
	dg, err := discordgo.New(token)
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

	if os.Getenv("CI") == "" && os.Getenv("GITHUB_ACTION") == "" {
		<-_continue
	}

	fmt.Println("Shutting down Discord Harmonbot Listener...")

	// Close connections
	if dgv != nil {
		dgv.Close()
	}
	dg.Close()

	return
}

func ready(s *discordgo.Session, event *discordgo.Ready) {
	s.UpdateStreamingStatus(0, "with Harmonbot", "https://www.twitch.tv/harmonbot")
}

func messageCreate(s *discordgo.Session, m *discordgo.MessageCreate) {
	var err error
	switch m.Content {
	case ">test":
		s.ChannelMessageSend(m.ChannelID, "Hello, World!")
	case "!help":
		s.ChannelMessageSend(m.ChannelID, "My prefix is `>`\nSee `>help`")
	case ">help":
		s.ChannelMessageSend(m.ChannelID, "WIP\n```>test\n>join (voice channel ID)\n>leave\n>listen\n>stoplistening [>stopl]\n>restart```")
	case ">listen":
		if dgv == nil {
			s.ChannelMessageSend(m.ChannelID, "I'm not in a voice channel\nUse `>join (voice channel ID)`")
		} else {
			_listen = true
			s.ChannelMessageSend(m.ChannelID, ":ear::skin-tone-2: I'm listening..")
			Listen(dgv)
			s.ChannelMessageSend(m.ChannelID, ":stop_sign: I stopped listening")
			// s.ChannelMessageEdit(m.ChannelID, response.ID, "I stopped listening")
		}
	case ">stopl", ">stoplistening":
		// response, err = s.ChannelMessageSend(m.ChannelID, "Processing..")
		// check(err)
		_listen = false
	case ">leave":
		err = dgv.Disconnect()
		check(err)
		dgv = nil
		s.ChannelMessageSend(m.ChannelID, ":door: I've left the voice channel")
	case ">restart":
		// if m.Author.ID == owner_id {
		s.ChannelMessageSend(m.ChannelID, ":ok_hand::skin-tone-2: Restarting...")
		close(_continue)
		// }
	case ">updateavatar":
		if m.Author.ID == owner_id {
			changeAvatar(s)
			s.ChannelMessageSend(m.ChannelID, "Avatar Updated")
		}
	case ">version go":
		s.ChannelMessageSend(m.ChannelID, runtime.Version())
	}
	if strings.HasPrefix(m.Content, ">join") {

		if recv != nil || send != nil {
			s.ChannelMessageSend(m.ChannelID, ":warning: Error: Please `>restart` me to have me rejoin")
			return
		}

		channel, err := s.Channel(m.ChannelID)
		check(err)
		if len(strings.Split(m.Content, " ")) == 1 {
			s.ChannelMessageSend(m.ChannelID, ":warning: Error: Please input the voice channel ID")
			return
		}
		dgv, err = s.ChannelVoiceJoin(channel.GuildID, strings.Split(m.Content, " ")[1], false, false)
		if err != nil {
			s.ChannelMessageSend(m.ChannelID, ":warning: Error")
			return
		}

		recv = make(chan *discordgo.Packet, 2)
		go dgvoice.ReceivePCM(dgv, recv)
		send = make(chan []int16, 2)
		go dgvoice.SendPCM(dgv, send)

		s.ChannelMessageSend(m.ChannelID, "I've joined the voice channel")
	}
}

func Listen(v *discordgo.VoiceConnection) {
	// fmt.Println("Echoing")

	fo, err := os.Create("data/temp/heard.pcm")
	check(err)

	// v.Speaking(true)
	// defer v.Speaking(false)

	w := bufio.NewWriter(fo)
	buf := new(bytes.Buffer)

	for _listen {
		p, ok := <-recv
		if !ok {
			return
		}

		// echo for debugging
		// send <- p.PCM
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
	img, err := ioutil.ReadFile("data/avatars/discord_harmonbot_listener_icon.png")
	check(err)
	// add file name input

	base64 := base64.StdEncoding.EncodeToString(img)

	avatar := fmt.Sprintf("data:image/png;base64,%s", string(base64))

	_, err = s.UserUpdate(me.Username, avatar)
	check(err)
}
