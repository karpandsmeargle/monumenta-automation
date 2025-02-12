use monumenta::player::Player;

use anyhow;
use redis::Commands;
use redis::RedisError;
use simplelog::*;
use uuid::Uuid;

use std::{env, thread};

macro_rules! map(
    { $($key:expr => $value:expr),+ } => {
        {
            let mut m = ::std::collections::HashMap::new();
            $(
                m.insert($key, $value);
            )+
            m
        }
     };
);

fn main() -> anyhow::Result<()> {
    let changes = map!(
        "0x26e" => 4,
        "1n10" => 37,
        "2ski" => 6,
        "3sqi" => 8,
        "6iq_" => 17,
        "8eyes" => 35,
        "8lam" => 13,
        "8xien8" => 9,
        "AAAAAA_Ming" => 8,
        "AAAMING" => 1,
        "ACubist" => 2,
        "AQE7" => 2,
        "Aba123" => 3,
        "Abstergos" => 16,
        "AbyssFir3" => 4,
        "AdrianPaint" => 19,
        "Aether_927" => 2,
        "AftershockLyn" => 12,
        "Alan_Is_Bored" => 117,
        "Alien_Villager" => 12,
        "Alittar" => 31,
        "AlterSorcerer" => 2,
        "AmbassadorArcant" => 74,
        "AngeloLagusa" => 2,
        "Anoma_" => 4,
        "Anthelmaz" => 2,
        "Aonq" => 1,
        "AramilNuren" => 108,
        "ArcaneBeamed" => 10,
        "Archemiendo" => 1,
        "Artifice42" => 32,
        "Asayus0" => 6,
        "AtanasTDB" => 23,
        "Aurabolt" => 1,
        "Avrial" => 2,
        "Azhan" => 21,
        "Azolattes" => 1,
        "B1dd" => 3,
        "BBQdPotato" => 3,
        "B_G_YG" => 44,
        "BaconGameMaster" => 1,
        "BadCatn" => 113,
        "Badbird" => 113,
        "BeastMasterFTW" => 5,
        "Bemo97" => 41,
        "Binsi" => 9,
        "Biw_" => 27,
        "BlackHeart2312" => 2,
        "BlackStenius" => 2,
        "Blendedwing797" => 4,
        "BlonZo" => 2,
        "BloodBlackMoon" => 1,
        "BobbyJonesSr" => 3,
        "BoganC" => 18,
        "Br1xx" => 56,
        "Bubignao" => 9,
        "Buck2700" => 260,
        "BulkyChihuahua" => 28,
        "BumBumOwO" => 125,
        "Buniiech" => 150,
        "BurntWaffles69" => 147,
        "Butcherberries" => 3,
        "CIA95" => 1,
        "CS_Aristotle" => 99,
        "CantaloupeGang" => 8,
        "CaptainJR" => 41,
        "CatProductions" => 15,
        "Cat_cake" => 7,
        "Catolax" => 38,
        "Chiinox_" => 167,
        "Civtac" => 1,
        "Cocona20xx" => 7,
        "ColorNight3031" => 3,
        "Combustible" => 44,
        "Complex_Ape" => 3,
        "Compsogbrickus" => 33,
        "Coolk1ng" => 13,
        "CottonR_" => 1,
        "CountTolvaly" => 13,
        "Creeepled" => 5,
        "CreepSlayerz" => 72,
        "Crevasse_" => 26,
        "CringeAura" => 311,
        "Cryonyxium" => 3,
        "Cryptic87" => 1,
        "CuriousYoungster" => 11,
        "Cyrelc" => 17,
        "DDeine" => 22,
        "DailyDecay" => 119,
        "DanielbombBeast" => 15,
        "Darklaser72" => 26,
        "Darmorel" => 35,
        "DataCrusader" => 53,
        "Dayablep" => 200,
        "Demilock" => 8,
        "Derailious" => 168,
        "Derpical" => 9,
        "Des_01" => 2,
        "Diego0552" => 34,
        "Dinobat" => 1,
        "Divzer" => 2,
        "DolphDaOne" => 131,
        "Dougan_jackjack" => 43,
        "DrDisRespect_" => 3,
        "Dr_B_Bones" => 4,
        "Dr_Beta" => 8,
        "Drdooms7" => 7,
        "Drekisol" => 2,
        "DuskPyramid" => 79,
        "Eb_" => 32,
        "Eddison_" => 207,
        "Elementlover" => 165,
        "Elsfic" => 13,
        "EmeraldVisions" => 208,
        "Endless_Shart" => 59,
        "EnragedRabisu" => 29,
        "Enter_Code" => 10,
        "Esciura" => 149,
        "Esdecay" => 8,
        "Exalted_King" => 2,
        "FakeKing02" => 8,
        "Familyski" => 3,
        "Fangride" => 7,
        "Fataled" => 12,
        "Ferwolf" => 13,
        "FieryChomper" => 32,
        "Firestorm256" => 2,
        "Fishy_cookies" => 3,
        "Flare_Calliope" => 11,
        "Fogfun" => 15,
        "Forite" => 1,
        "Foxen21" => 5,
        "FrenchFries233" => 12,
        "Fropperoni" => 84,
        "FrostedSyCo" => 1,
        "Frostvenom795" => 85,
        "Fwap_a_Durp" => 492,
        "G3m1n1Boy" => 18,
        "G_XiaoHua" => 17,
        "GameSebas256" => 30,
        "Gaynesis" => 71,
        "Geci1000" => 2,
        "GetZoinked" => 138,
        "Glenz" => 8,
        "Golden_Paladin" => 25,
        "Grayfirebird" => 5,
        "GreenTEA6666" => 5,
        "H4TO" => 11,
        "HV_Metal" => 15,
        "Hallownest__" => 24,
        "Hap_pyAlex" => 5,
        "Hawaiinate" => 20,
        "Haxorzist" => 169,
        "HaydanLe" => 7,
        "Hazerdous" => 6,
        "Headstool" => 27,
        "Hechnoderp" => 43,
        "HeerCasper" => 10,
        "Highmore" => 103,
        "HohoCookie620" => 1,
        "Humbirds" => 23,
        "HungHeretic" => 6,
        "Hxxc2333" => 19,
        "Hydrafang" => 49,
        "ISA_x_JAKE" => 16,
        "I_Vuken_I" => 28,
        "IamKinKin" => 5,
        "IcebergLettuce47" => 150,
        "Icely_Done" => 21,
        "IcyWind88" => 5,
        "Icycl" => 57,
        "Ignys" => 48,
        "ImLikeSoCat" => 12,
        "Indestria" => 13,
        "ItsDatBunneh" => 5,
        "ItsDrag0n" => 106,
        "Its_Nebz" => 199,
        "ItsaOreo" => 8,
        "Itsrasertop" => 31,
        "ItzButterBall" => 5,
        "JAY_zixuan" => 86,
        "JH0lla" => 2,
        "Jahmohn" => 7,
        "Jammy_Pingu" => 1,
        "Jarraxitty" => 7,
        "Jerry_Na" => 11,
        "Jillzippy" => 145,
        "Joan055" => 37,
        "Joeysir" => 3,
        "Joshyckel" => 1,
        "Jtree" => 210,
        "JudicialGiraffe" => 43,
        "JuicedBananas" => 86,
        "Justicesaur" => 3,
        "KC_AfterDark" => 21,
        "KH2Roxas" => 11,
        "KJure" => 1,
        "Keick" => 3,
        "Kingofcows76" => 86,
        "Klaurial" => 67,
        "Kleg" => 1,
        "Kohoyo" => 38,
        "Kuyuuma" => 4,
        "Kyress" => 20,
        "LSY_forever" => 9,
        "Laapsap" => 91,
        "Leggoboyi" => 26,
        "Legro8" => 65,
        "Leiyam" => 72,
        "LeleJLs" => 2,
        "Leo_Percy" => 1,
        "Leous" => 25,
        "Lewdentry" => 13,
        "LightningGem23" => 7,
        "Lightning_Boy" => 36,
        "LilVincie" => 14,
        "LoL_Bite" => 8,
        "LordGeek101" => 474,
        "LordHokage_" => 79,
        "LowHeights" => 3,
        "LuUrk_RV_Roy" => 4,
        "LukyBaluki" => 1,
        "Lunar654" => 18,
        "Lyon2345" => 43,
        "M3_G4" => 2,
        "MN_128" => 2,
        "MagicalShark" => 34,
        "Mah0" => 5,
        "Mandolino17" => 10,
        "MatixD26" => 151,
        "Mehaz" => 39,
        "Mehdes" => 3,
        "Melancholiy" => 60,
        "Melonxd57894" => 12,
        "MemeLordTheThird" => 80,
        "Memoiresse" => 1,
        "MeowyChu" => 11,
        "Meronakai" => 2,
        "MerryTacos" => 30,
        "Michael228p" => 50,
        "Mikara_" => 141,
        "MikuClient" => 1,
        "Mimi_29" => 57,
        "Mine_Hinata" => 49,
        "MintedTea" => 1,
        "Mitsue_e" => 16,
        "MorriganMo" => 3,
        "MrBSPetaByte" => 101,
        "Nabsin" => 148,
        "NebulaeBee" => 5,
        "NickNackGus" => 7,
        "NightMessenger" => 90,
        "Nightsheaulan" => 2,
        "Nikolas_0113" => 3,
        "Njol" => 208,
        "NobodyPi" => 172,
        "Noellee_" => 104,
        "Nolvid" => 3,
        "Noodlas_" => 141,
        "NookPlayz" => 44,
        "NouamaneM762" => 5,
        "OOO6704" => 1,
        "Omsitua" => 8,
        "OneLord" => 16,
        "Pacific_Legend" => 115,
        "PacifismBebu" => 131,
        "Pakstf" => 78,
        "Palaeontological" => 24,
        "Panda_Pendulum" => 4,
        "PandicornioLn" => 39,
        "Panosdim05" => 1,
        "Parallax__" => 6,
        "Parazones" => 7,
        "Payhi25" => 61,
        "PearUhDox" => 37,
        "Phatwick" => 45,
        "Pikachews" => 15,
        "Pizzatiger" => 1,
        "PockyTakeo" => 1,
        "PolarBear579" => 34,
        "Ponkibg" => 5,
        "Popcrash" => 47,
        "Poratoe" => 67,
        "PorterVisions" => 14,
        "Pqinless" => 1,
        "Praetle" => 1,
        "Pudding_O3O" => 14,
        "PufferFish_420" => 110,
        "Python2207" => 313,
        "Pythraithia" => 13,
        "QY6" => 5,
        "QooQooApple" => 64,
        "Qweun" => 17,
        "RBT_Fireball" => 127,
        "RainDream" => 178,
        "Rain_stxrm" => 9,
        "Rainbow_loyalty" => 20,
        "RainieMan" => 3,
        "Raisin5488" => 144,
        "RarioTrarioWario" => 4,
        "Re1f" => 5,
        "RegularDave" => 19,
        "RenZenthio" => 6,
        "RevenantHorror" => 167,
        "Rhinowo" => 20,
        "RiggaParty" => 1,
        "RockNRed" => 60,
        "Rocket_Ivan" => 44,
        "Rodogorgon" => 26,
        "Rubiks_Creeper" => 38,
        "Rum__" => 5,
        "SV_Bluesky" => 14,
        "SadDingus" => 74,
        "SamTheWatermelon" => 10,
        "SanjiThree" => 4,
        "Scepticism_" => 2,
        "ScryingStan" => 3,
        "ShadeOfRegret" => 4,
        "ShadowVisions" => 86,
        "SharkTech" => 8,
        "SharkYEe" => 16,
        "Shinn_Kenn" => 44,
        "Shinycolors" => 17,
        "Shmoofly" => 62,
        "Shushi_794" => 1,
        "SikaBg" => 46,
        "SilentCow88" => 82,
        "SilverPoison" => 132,
        "SirTudor" => 10,
        "Siravia" => 1,
        "Sky_3" => 18,
        "Sky_Hope_134" => 3,
        "Sky_Watcher" => 27,
        "Skyzor" => 86,
        "SleepingRaven" => 19,
        "SlimeKing77777" => 52,
        "Slothy55" => 5,
        "Slykas" => 3,
        "Slyyam" => 84,
        "SmiGuy" => 139,
        "SomePolarBear" => 35,
        "SorcererAxis81" => 203,
        "Soso12yt" => 19,
        "Soup" => 107,
        "Sparklepop" => 11,
        "SphorUs" => 93,
        "SpoonMor" => 1,
        "Spy21DD" => 168,
        "Squidish" => 2,
        "Start280Finish" => 3,
        "StealthyVisions" => 21,
        "Sukie" => 34,
        "SunnyVisions" => 19,
        "Superman4252" => 38,
        "SuzunaAoi" => 11,
        "Svelton" => 77,
        "TKTOM7" => 250,
        "Tatsu43" => 52,
        "Teewie" => 11,
        "TheCEOofShaqland" => 2,
        "TheCrusader57" => 140,
        "TheKhaaang" => 1,
        "TheMonarchAwaken" => 133,
        "TheSuperDuper7" => 1,
        "The_Gemgamer" => 3,
        "The_Sorcerer" => 5,
        "TokenBoost" => 112,
        "Tom_VN" => 4,
        "TorrentialPie" => 158,
        "TortillaEpicee" => 2,
        "Tostitokid259" => 7,
        "Trans_Rites" => 41,
        "TrickishBlake204" => 2,
        "TropicalVisions" => 28,
        "TrueConstitution" => 22,
        "Tryke_O" => 10,
        "TuckAttack" => 2,
        "TuckerThePenguin" => 5,
        "Tuli_Lintu" => 73,
        "TweeteaC" => 29,
        "Tyler14a" => 24,
        "Vanguard1404" => 3,
        "Vasque" => 4,
        "VastPoenBV" => 41,
        "Vince0909" => 140,
        "Vladomeme" => 13,
        "VolatileAnomaly" => 86,
        "WIIPNIP" => 2,
        "Warwolf595" => 26,
        "Wembler" => 180,
        "Whatthe345" => 1,
        "Whitebeard_OP" => 1,
        "Whitswor" => 6,
        "WillowxD" => 63,
        "WitherChrono" => 1,
        "Wolfhog" => 53,
        "WxAaRoNxW" => 19,
        "Xcela" => 12,
        "Xeabia" => 55,
        "Xeronsis" => 128,
        "Xi_shan2" => 5,
        "XtraKrispy_" => 8,
        "XxProCrusherxX" => 10,
        "YMCatlord" => 9,
        "Yaer_" => 5,
        "Yandere" => 10,
        "YellowGuyXD" => 14,
        "YenYuu" => 1,
        "Yurikiro" => 6,
        "ZKirederf" => 8,
        "Zain1" => 2,
        "ZerVisions" => 75,
        "Zerodeta" => 110,
        "Ziggles_" => 10,
        "Zomplee" => 22,
        "Zouba64" => 71,
        "Zqroz" => 64,
        "Zu_Kompliziert" => 34,
        "Zyreon" => 78,
        "_Ako_Tako" => 45,
        "_M1cro" => 50,
        "_Nanasi" => 15,
        "_Noxington_" => 4,
        "_Sazra" => 47,
        "_SpeedDragon_" => 41,
        "_Stickers1342" => 3,
        "_YungGravy" => 6,
        "__Deen__" => 154,
        "__Kiro__" => 26,
        "__Nover" => 1,
        "_wu_feng_" => 183,
        "aGrxpe" => 79,
        "activecircuit" => 36,
        "ajdude9" => 90,
        "ajfish" => 5,
        "andrew3984" => 3,
        "aokirikoya" => 139,
        "awalterskong" => 2,
        "bananaice" => 34,
        "benikirara" => 6,
        "benito_bodoke" => 22,
        "binches" => 21,
        "blondeboy1" => 4,
        "bonnyplanki" => 41,
        "bruhily" => 32,
        "bumky" => 2,
        "burgerbun" => 5,
        "c8corvette" => 5,
        "carefreemiau" => 25,
        "cartsinabag" => 252,
        "chrysitis" => 2,
        "chuwenhsuan" => 221,
        "clubhouse_" => 4,
        "cocopad" => 186,
        "creepTNT" => 15,
        "crystal5236" => 80,
        "cuickbrownfox" => 4,
        "cyndal_" => 1,
        "daaaaaa645" => 13,
        "darkerguy2634" => 7,
        "darknee" => 94,
        "dash10138" => 11,
        "deripy" => 2,
        "devi_birb" => 6,
        "diamondinferno1" => 40,
        "dogaly" => 20,
        "doop1051" => 110,
        "dqvii" => 5,
        "dragonlord9876" => 5,
        "dunnie48" => 10,
        "elicop" => 10,
        "emilyloaf" => 38,
        "emmilytvisafurry" => 36,
        "enzosoAWESOME" => 1,
        "enzosoEPIC" => 27,
        "er3222" => 116,
        "euxrcn" => 43,
        "fan_chenn" => 7,
        "firedfish337" => 2,
        "foodenjoyer" => 4,
        "forte927" => 115,
        "foxilvery" => 13,
        "frogyfro" => 15,
        "g3p0" => 7,
        "garvenator43" => 2,
        "gasp97" => 153,
        "gizmo90704" => 50,
        "gnarzy" => 71,
        "guipiralho9" => 26,
        "helphelp11" => 23,
        "hi529" => 3,
        "hppeng" => 3,
        "hungerpangs" => 8,
        "hypeace" => 71,
        "idkpangs" => 51,
        "ienjoycatgirls" => 1,
        "iiJei" => 14,
        "ik1ra" => 8,
        "imfron" => 5,
        "indw" => 21,
        "jeqi" => 7,
        "jjking80" => 33,
        "jordoh" => 26,
        "kabotyaneko" => 31,
        "kadinhou" => 25,
        "kakq" => 6,
        "kcalBBlack" => 108,
        "kehyan" => 2,
        "kerokeros" => 1,
        "khan6308" => 8,
        "kitchenwarrior" => 121,
        "knifefan" => 7,
        "koreyou" => 6,
        "linzefeng" => 40,
        "littleprincess98" => 6,
        "lky_kelvin" => 4,
        "lukeandmatthew" => 5,
        "marry13" => 19,
        "mialovly" => 2,
        "michi_4171" => 3,
        "michthemoo" => 148,
        "microlmao" => 10,
        "minerdwarf222" => 179,
        "ming0328ming" => 57,
        "moonberserker" => 146,
        "motorizedcat" => 1,
        "mscr" => 16,
        "needmoney90" => 227,
        "nicknon" => 139,
        "nitro1992" => 6,
        "niwatori222" => 31,
        "not_a_noob_21" => 1,
        "notrobi" => 5,
        "notxcarter" => 144,
        "o3oKarl" => 41,
        "ohSauce" => 93,
        "ohayoo" => 92,
        "ooAddman" => 73,
        "ooMorgan" => 15,
        "owoop" => 121,
        "panderz14" => 149,
        "peachy_sky" => 1,
        "pertz" => 3,
        "phebelia" => 98,
        "pottedplant530" => 133,
        "prets" => 532,
        "puppylover798" => 2,
        "quackqwack_" => 221,
        "qvoi" => 1,
        "raecat23" => 27,
        "rainbowx1994" => 17,
        "rayman520" => 10,
        "refortor" => 28,
        "resonate01" => 63,
        "ronkontel" => 6,
        "rozteddy" => 28,
        "rsflicker" => 164,
        "sSpiike" => 5,
        "shman" => 8,
        "silvervalley" => 3,
        "sjasogun" => 64,
        "sloppyyyyyy" => 5,
        "smileQwanton" => 1,
        "smilerdeadly" => 19,
        "snscl" => 6,
        "spearmkw" => 194,
        "spoopykay" => 9,
        "squirrr" => 8,
        "such_sussy_baka" => 17,
        "taaara" => 32,
        "temis" => 18,
        "theeJRook" => 108,
        "theman13579" => 5,
        "thetruebot" => 15,
        "thololer" => 1,
        "thom_shadow" => 5,
        "treebeard68" => 1,
        "tyehua" => 22,
        "ufutgs" => 4,
        "uwuZalia" => 194,
        "vinc_ohi" => 16,
        "waiwai_923" => 2,
        "wearecrafty" => 81,
        "whyprophecy" => 105,
        "williamcheese" => 8,
        "wim1994" => 16,
        "woeuq" => 5,
        "xAvocqdo" => 29,
        "xBrae" => 134,
        "xEpicB" => 98,
        "x_Fallen_Angel_x" => 35,
        "yetanotherday" => 15,
        "zMichisan" => 7,
        "zdtsd" => 74,
        "zwrbowo" => 172
    );

    let mut multiple = vec![];
    match TermLogger::new(LevelFilter::Debug, Config::default(), TerminalMode::Mixed) {
        Some(logger) => multiple.push(logger as Box<dyn SharedLogger>),
        None => multiple.push(SimpleLogger::new(LevelFilter::Debug, Config::default())),
    }
    CombinedLogger::init(multiple).unwrap();

    let mut args: Vec<String> = env::args().collect();

    if args.len() != 1 {
        println!("Usage: redis_reset_scores");
        return Ok(());
    }

    args.remove(0);

    let domain = "play";
    let objective = "HorsemanWins";
    let history = "Reverted HorsemanWins";
    let mut threads = vec![];

    for (playername, add_val) in changes {
        let thread = thread::spawn(move || {
            let client = redis::Client::open("redis://127.0.0.1/");
            if let Err(redis_err) = client {
                println!("Failed to create client to redis: {}", redis_err);
            } else if let Ok(client) = client {
                let con: Result<redis::Connection, RedisError> = client.get_connection();
                if let Err(redis_err) = con {
                    println!("Failed to connect to redis: {}", redis_err);
                } else if let Ok(mut con) = con {
                    // println!("Loading {}", playername);
                    let uuid_result: Result<String, RedisError> =
                        con.hget("name2uuid", playername.to_string());
                    if let Ok(uuid_str) = uuid_result {
                        let uuid: Uuid = Uuid::parse_str(&uuid_str).unwrap();

                        let mut player = Player::new(uuid);
                        if let Err(redis_err) = player.load_redis(&domain, &mut con) {
                            println!("Failed to load player data {} : {}", playername, redis_err);
                        } else {
                            if let Some(scores) = &mut player.scores {
                                // NOTE: Set value, not add!
                                let new_score = add_val;
                                scores.insert(objective.to_string(), new_score);
                                player.update_history(history);
                                if let Err(redis_err) = player.save_redis(&domain, &mut con) {
                                    println!(
                                        "Failed to save player data {} : {}",
                                        playername, redis_err
                                    );
                                }
                            }
                            println!("{}", player);
                        }
                    } else if let Err(redis_err) = uuid_result {
                        println!("Failed to parse {} : {}", playername, redis_err);
                    }
                }
            }
        });
        threads.push(thread);
    }

    for thread in threads {
        thread.join();
    }

    Ok(())
}
