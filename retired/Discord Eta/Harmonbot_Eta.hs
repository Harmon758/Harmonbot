{-# LANGUAGE OverloadedStrings, RecordWildCards, MultiWayIf #-}
import Data.Text as T hiding (intercalate)
import Pipes

import Network.Discord
import Language.Discord

import GHC.Stats

import Network.WebSockets

-- import Paths_discord_hs (version)
import Data.Version (showVersion)

import Data.List (intercalate)

-- 0.1.2

reply :: Network.Discord.Message -> Text -> Effect DiscordM ()
reply Message{messageChannel=chan} cont = fetch' $ CreateMessage chan cont

updateStatus :: String -> Effect DiscordM ()
updateStatus status = do
  DiscordState _ _ ws _ _ <- get
  liftIO . sendTextData ws $ StatusUpdate Nothing (Just status)

main :: IO ()
main = runBot "BOT TOKEN" $ do
  with ReadyEvent $ \(Init v u _ _ _) -> do
    liftIO . putStrLn $ "Connected to gateway v" ++ show v ++ " as user " ++ show u
    updateStatus "with Harmonbot"

  with MessageCreateEvent $ \msg@Message{..} -> do
    when (not . userIsBot $ messageAuthor) $ 
      if | "+test" `isPrefixOf` messageContent -> do
           reply msg "Hello, World!"
         -- | "+info" `isPrefixOf` messageContent -> do
           -- GCStats{..} <- liftIO $ getGCStats
           -- reply msg . pack $ intercalate "\n" [
             --   "```yaml"
             -- , "Lambdacord: https://gitlab.com/jkoike/lambdacord"
             -- , "Version: " ++ showVersion version
             -- , "Peak memory: " ++ show maxBytesUsed
             -- , "Current memory: " ++ show currentBytesUsed
             -- , "Uptime: " ++ show wallSeconds
             -- , "CPU time: " ++ show cpuSeconds
             -- , "GC CPU time: " ++ show gcCpuSeconds
             -- , "```"
             -- ]
           -- "Discord.hs v" ++ showVersion version
         | otherwise -> return ()

