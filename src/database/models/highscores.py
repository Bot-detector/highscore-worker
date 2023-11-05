from sqlalchemy import (
    BigInteger,
    Column,
    Date,
    DateTime,
    ForeignKeyConstraint,
    Integer,
    UniqueConstraint,
    func,
)

from src.database.database import Base


class PlayerHiscoreData(Base):
    __tablename__ = "playerHiscoreData"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, server_default=func.now())
    ts_date = Column(Date, nullable=True)
    Player_id = Column(Integer, nullable=False)
    total = Column(BigInteger, default=0)
    attack = Column(Integer, default=0)
    defence = Column(Integer, default=0)
    strength = Column(Integer, default=0)
    hitpoints = Column(Integer, default=0)
    ranged = Column(Integer, default=0)
    prayer = Column(Integer, default=0)
    magic = Column(Integer, default=0)
    cooking = Column(Integer, default=0)
    woodcutting = Column(Integer, default=0)
    fletching = Column(Integer, default=0)
    fishing = Column(Integer, default=0)
    firemaking = Column(Integer, default=0)
    crafting = Column(Integer, default=0)
    smithing = Column(Integer, default=0)
    mining = Column(Integer, default=0)
    herblore = Column(Integer, default=0)
    agility = Column(Integer, default=0)
    thieving = Column(Integer, default=0)
    slayer = Column(Integer, default=0)
    farming = Column(Integer, default=0)
    runecraft = Column(Integer, default=0)
    hunter = Column(Integer, default=0)
    construction = Column(Integer, default=0)
    league = Column(Integer, default=0)
    bounty_hunter_hunter = Column(Integer, default=0)
    bounty_hunter_rogue = Column(Integer, default=0)
    cs_all = Column(Integer, default=0)
    cs_beginner = Column(Integer, default=0)
    cs_easy = Column(Integer, default=0)
    cs_medium = Column(Integer, default=0)
    cs_hard = Column(Integer, default=0)
    cs_elite = Column(Integer, default=0)
    cs_master = Column(Integer, default=0)
    lms_rank = Column(Integer, default=0)
    soul_wars_zeal = Column(Integer, default=0)
    abyssal_sire = Column(Integer, default=0)
    alchemical_hydra = Column(Integer, default=0)
    barrows_chests = Column(Integer, default=0)
    bryophyta = Column(Integer, default=0)
    callisto = Column(Integer, default=0)
    cerberus = Column(Integer, default=0)
    chambers_of_xeric = Column(Integer, default=0)
    chambers_of_xeric_challenge_mode = Column(Integer, default=0)
    chaos_elemental = Column(Integer, default=0)
    chaos_fanatic = Column(Integer, default=0)
    commander_zilyana = Column(Integer, default=0)
    corporeal_beast = Column(Integer, default=0)
    crazy_archaeologist = Column(Integer, default=0)
    dagannoth_prime = Column(Integer, default=0)
    dagannoth_rex = Column(Integer, default=0)
    dagannoth_supreme = Column(Integer, default=0)
    deranged_archaeologist = Column(Integer, default=0)
    general_graardor = Column(Integer, default=0)
    giant_mole = Column(Integer, default=0)
    grotesque_guardians = Column(Integer, default=0)
    hespori = Column(Integer, default=0)
    kalphite_queen = Column(Integer, default=0)
    king_black_dragon = Column(Integer, default=0)
    kraken = Column(Integer, default=0)
    kreearra = Column(Integer, default=0)
    kril_tsutsaroth = Column(Integer, default=0)
    mimic = Column(Integer, default=0)
    nex = Column(Integer, default=0)
    nightmare = Column(Integer, default=0)
    phosanis_nightmare = Column(Integer, default=0)
    obor = Column(Integer, default=0)
    phantom_muspah = Column(Integer, default=0)
    sarachnis = Column(Integer, default=0)
    scorpia = Column(Integer, default=0)
    skotizo = Column(Integer, default=0)
    tempoross = Column(Integer, default=0)
    the_gauntlet = Column(Integer, default=0)
    the_corrupted_gauntlet = Column(Integer, default=0)
    theatre_of_blood = Column(Integer, default=0)
    theatre_of_blood_hard = Column(Integer, default=0)
    thermonuclear_smoke_devil = Column(Integer, default=0)
    tombs_of_amascut = Column(Integer, default=0)
    tombs_of_amascut_expert = Column(Integer, default=0)
    tzkal_zuk = Column(Integer, default=0)
    tztok_jad = Column(Integer, default=0)
    venenatis = Column(Integer, default=0)
    vetion = Column(Integer, default=0)
    vorkath = Column(Integer, default=0)
    wintertodt = Column(Integer, default=0)
    zalcano = Column(Integer, default=0)
    zulrah = Column(Integer, default=0)
    rifts_closed = Column(Integer, default=0)
    artio = Column(Integer, default=0)
    calvarion = Column(Integer, default=0)
    duke_sucellus = Column(Integer, default=0)
    spindel = Column(Integer, default=0)
    the_leviathan = Column(Integer, default=0)
    the_whisperer = Column(Integer, default=0)
    vardorvis = Column(Integer, default=0)

    # Constraints for unique keys and foreign key
    __table_args__ = (
        UniqueConstraint(
            "Player_id", "timestamp", name="idx_playerHiscoreData_Player_id_timestamp"
        ),
        UniqueConstraint("Player_id", "ts_date", name="Unique_player_date"),
        ForeignKeyConstraint(
            ["Player_id"],
            ["Players.id"],
            name="FK_Players_id",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
    )
