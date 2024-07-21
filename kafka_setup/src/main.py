import json
import os
import random
from datetime import datetime, timedelta

import _kafka_config
from kafka import KafkaProducer


def send_data(producer: KafkaProducer):
    example_player = {
        "id": 0,
        "name": "",
        "created_at": "2023-06-16T12:17:53",
        "updated_at": "2024-07-17T03:14:59",
        "possible_ban": 0,
        "confirmed_ban": 0,
        "confirmed_player": 0,
        "label_id": 0,
        "label_jagex": 0,
    }
    example_hs = {
        "attack": 0,
        "defence": 289052,
        "strength": 0,
        "hitpoints": 0,
        "ranged": 0,
        "prayer": 0,
        "magic": 0,
        "cooking": 0,
        "woodcutting": 0,
        "fletching": 0,
        "fishing": 0,
        "firemaking": 166655,
        "crafting": 166661,
        "smithing": 0,
        "mining": 0,
        "herblore": 0,
        "agility": 384304,
        "thieving": 0,
        "slayer": 0,
        "farming": 0,
        "runecraft": 0,
        "hunter": 0,
        "construction": 0,
        "total": 1006672,
        "league": 0,
        "deadman_points": 0,
        "bounty_hunter_hunter": 0,
        "bounty_hunter_rogue": 0,
        "bounty_hunter_legacy_hunter": 0,
        "bounty_hunter_legacy_rogue": 0,
        "cs_all": 0,
        "cs_beginner": 0,
        "cs_easy": 0,
        "cs_medium": 0,
        "cs_hard": 0,
        "cs_elite": 0,
        "cs_master": 0,
        "lms_rank": 0,
        "pvp_arena_rank": 0,
        "soul_wars_zeal": 0,
        "rifts_closed": 0,
        "colosseum_glory": 0,
        "abyssal_sire": 0,
        "alchemical_hydra": 0,
        "artio": 0,
        "barrows_chests": 0,
        "bryophyta": 0,
        "callisto": 0,
        "calvarion": 0,
        "cerberus": 0,
        "chambers_of_xeric": 0,
        "chambers_of_xeric_challenge_mode": 0,
        "chaos_elemental": 0,
        "chaos_fanatic": 0,
        "commander_zilyana": 0,
        "corporeal_beast": 0,
        "crazy_archaeologist": 0,
        "dagannoth_prime": 0,
        "dagannoth_rex": 0,
        "dagannoth_supreme": 0,
        "deranged_archaeologist": 0,
        "duke_sucellus": 0,
        "general_graardor": 0,
        "giant_mole": 0,
        "grotesque_guardians": 0,
        "hespori": 0,
        "kalphite_queen": 0,
        "king_black_dragon": 0,
        "kraken": 0,
        "kreearra": 0,
        "kril_tsutsaroth": 0,
        "lunar_chests": 0,
        "mimic": 0,
        "nex": 0,
        "nightmare": 0,
        "phosanis_nightmare": 0,
        "obor": 0,
        "phantom_muspah": 0,
        "sarachnis": 0,
        "scorpia": 0,
        "scurrius": 0,
        "skotizo": 0,
        "sol_heredit": 0,
        "spindel": 0,
        "tempoross": 0,
        "the_gauntlet": 0,
        "the_corrupted_gauntlet": 0,
        "the_leviathan": 0,
        "the_whisperer": 0,
        "theatre_of_blood": 0,
        "theatre_of_blood_hard": 0,
        "thermonuclear_smoke_devil": 0,
        "tombs_of_amascut": 0,
        "tombs_of_amascut_expert": 0,
        "tzkal_zuk": 0,
        "tztok_jad": 0,
        "vardorvis": 0,
        "venenatis": 0,
        "vetion": 0,
        "vorkath": 0,
        "wintertodt": 0,
        "zalcano": 0,
        "zulrah": 0,
    }
    example = {
        "player": {},
        "hiscores": {},
    }

    len_messages = 100_000
    players = [f"player{i}" for i in range(300)]
    for i in range(len_messages):
        player = random.choice(players)
        player_id = int(player.replace("player", ""))
        timestamp = datetime.now() - timedelta(
            days=random.randint(0, 360),
            hours=random.randint(0, 24),
        )
        timestamp = timestamp.isoformat()

        msg = {
            "player": {
                "id": player_id,
                "name": player,
                "created_at": "2023-06-16T12:17:53",
                "updated_at": timestamp,
                "possible_ban": 0,
                "confirmed_ban": 0,
                "confirmed_player": 0,
                "label_id": 0,
                "label_jagex": 0,
            },
            "hiscores": {
                k: random.randint(0, 200)
                * random.randint(0, 1000)
                * random.randint(0, 1000)
                for k, _ in example_hs.items()
            }
            | {"Player_id": player_id, "timestamp": timestamp},
        }
        print(i, msg)
        producer.send(topic="scraper", value=msg)


def main():
    _kafka_config.create_topics()
    # Get the Kafka broker address from the environment variable
    kafka_broker = os.environ.get("KAFKA_BROKER", "localhost:9094")

    # Create the Kafka producer
    producer = KafkaProducer(
        bootstrap_servers=kafka_broker,
        value_serializer=lambda x: json.dumps(x).encode(),
    )
    send_data(producer=producer)


if __name__ == "__main__":
    main()
