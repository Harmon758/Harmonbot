package main

import (
	"flag"
	"fmt"

	"github.com/bwmarrin/dgvoice"
	"github.com/bwmarrin/discordgo"
	
	"bufio"
	"bytes"
	// "io"
	"os"
	"encoding/binary"
	
	"keys"
)

var echo bool
var _dgv *discordgo.VoiceConnection
var _recv chan *discordgo.Packet
var _send chan []int16
var _continue bool

func main() {

	// NOTE: All of the below fields are required for this example to work correctly.
	var (
		// Email     = flag.String("e", "", "Discord account email.")
		// Password  = flag.String("p", "", "Discord account password.")
		Token     = flag.String("t", keys.Listener_token, "Discord account token.")
		GuildID   = flag.String("g", "147208000132743168", "Guild ID")
		ChannelID = flag.String("c", "181000982006595584", "Channel ID")
		err       error
	)
	flag.Parse()
	
	fmt.Println("Starting up Harmonbot Listener...")

	// Connect to Discord
	discord, err := discordgo.New(*Token)
	if err != nil {
		fmt.Println(err)
		return
	}
	
	discord.AddHandler(messageCreate)

	// Open Websocket
	err = discord.Open()
	if err != nil {
		fmt.Println(err)
		return
	}
	
	me, err := discord.User("@me")
	
	fmt.Printf("Started up %s#%s (%s)\n", me.Username, me.Discriminator, me.ID)

	// Connect to voice channel.
	// NOTE: Setting mute to false, deaf to true.
	dgv, err := discord.ChannelVoiceJoin(*GuildID, *ChannelID, false, false)
	if err != nil {
		fmt.Println(err)
		return
	}

	// Starts echo
	// Echo(dgv)
	
	recv := make(chan *discordgo.Packet, 2)
	go dgvoice.ReceivePCM(dgv, recv)
	
	send := make(chan []int16, 2)
	go dgvoice.SendPCM(dgv, send)
	
	_dgv = dgv
	_recv = recv
	_send = send
	
	// Simple way to keep program running until any key press.
	// var input string
	// fmt.Scanln(&input)
	
	_continue = true
	
	for _continue {}
	
	fmt.Println("Restarting Harmonbot Listener...")

	// ---logout
	discord.Logout()
	
	// Close connections
	dgv.Close()
	discord.Close()

	return
}

// Takes inbound audio and sends it right back out.
func Echo(v *discordgo.VoiceConnection) {

	fmt.Println("Echoing")
	
	fo, err := os.Create("data/testing.pcm")
	if err != nil {
		fmt.Println(err)
		return
	}

	v.Speaking(true)
	defer v.Speaking(false)
	
	w := bufio.NewWriter(fo)
	
	buf := new(bytes.Buffer)

	for echo {

		p, ok := <-_recv
		if !ok {
			return
		}

		_send <- p.PCM
		err := binary.Write(buf, binary.LittleEndian, p.PCM)
		if err != nil {
			fmt.Println(err)
			return
		}
		
	}
	
	_, err = w.Write(buf.Bytes())
		if err != nil {
			fmt.Println(err)
			return
		}
	
	err = w.Flush()
		if err != nil {
			fmt.Println(err)
			return
		}
	fo.Sync()
	
	fmt.Println("Stopping")
	
}

func messageCreate(s *discordgo.Session, m *discordgo.MessageCreate) {

	if m.Content == ">listen" {
		echo = true
		Echo(_dgv)
	} else if m.Content == ">stopl" {
		echo = false
	} else if m.Content == "!restartlistener" {
		_continue = false
	}
	// Print message to stdout.
	// fmt.Printf("%20s %20s %20s > %s\n", m.ChannelID, time.Now().Format(time.Stamp), m.Author.Username, m.Content)
}
