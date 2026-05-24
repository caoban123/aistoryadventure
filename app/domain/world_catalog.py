from __future__ import annotations

from app.domain.schemas import WorldCatalogItem


WORLD_CATALOG: tuple[WorldCatalogItem, ...] = (
    WorldCatalogItem(
        id="sunless-realm",
        title="The Sunless Realm",
        mode="Adventure",
        description=(
            "A cursed kingdom where the sun vanished thirty years ago and every "
            "lantern is fed by memory."
        ),
        image=(
            "linear-gradient(90deg, rgba(0,0,0,.78), rgba(0,0,0,.28)), "
            "url('./assets/world-sunless-realm.png')"
        ),
        tags=["Dark Fantasy", "Memory", "Cursed Kingdom"],
        world_seed=(
            "Da Thanh is a kingdom where the sun has not risen for thirty years. "
            "Its lanterns burn human memories for light, and the poor trade "
            "childhood fragments while the Lantern Council watches through every flame."
        ),
        long_description=(
            "Da Thanh is a kingdom where the sun has not risen for thirty years. "
            "The only light comes from lanterns fueled by human memory. Every hour "
            "of light burns away a remembered face, song, or childhood moment. The "
            "rich own hundreds of lanterns; the poor guard a single flame. Children "
            "are forced to sell memories to illuminate noble estates, and the seven "
            "elders of the Lantern Council, who have no memories left, see the whole "
            "realm through borrowed light. Rumors point below the Nameless Quarter, "
            "where an eternal lantern may be burning on the memory of an erased people."
        ),
    ),
    WorldCatalogItem(
        id="memory-market",
        title="The Memory Market",
        mode="Novel",
        description=(
            "A city where memories are bottled, traded, stolen, and used as currency."
        ),
        image=(
            "linear-gradient(135deg, rgba(10,12,18,.3), rgba(0,0,0,.7)), "
            "url('./assets/world-memory.png')"
        ),
        tags=["Novel", "Memory Trade", "Urban Fantasy"],
        world_seed=(
            "In a city built around bottled memories, identity is currency. "
            "Merchants sell first kisses, thieves steal grief, and the protagonist "
            "discovers a memory that proves their life was edited."
        ),
        long_description=(
            "The Memory Market is a city of glass vials, sealed recollections, and "
            "quiet auction rooms where people buy courage, sell grief, and pawn "
            "entire years to survive. The most valuable goods are not treasures but "
            "proofs of self: the memory of a parent's voice, a betrayal, a murder, "
            "or a love that never happened. Beneath the market runs a forbidden "
            "exchange for stolen identities, and every bottle there carries a price "
            "beyond money. The story begins when a memory appears that should belong "
            "to the protagonist, but shows a life they do not remember living."
        ),
    ),
    WorldCatalogItem(
        id="ashen-archive",
        title="The Ashen Archive",
        mode="Novel",
        description="A forbidden library records futures that have not happened yet.",
        image=(
            "linear-gradient(135deg, rgba(10,12,18,.3), rgba(0,0,0,.7)), "
            "url('./assets/world-archive.png')"
        ),
        tags=["Forbidden Library", "Future", "Dark Academia"],
        world_seed=(
            "At the edge of a decaying empire stands the Ashen Archive, a library "
            "of futures that never happened. To read one, you must burn it, erasing "
            "that possibility forever."
        ),
        long_description=(
            "At the edge of a decaying empire stands the Ashen Archive, a forbidden "
            "library containing books that record futures which have not happened. "
            "Each book is made from the ash of beings who dreamed that possible "
            "future. To read a volume, a visitor must burn it; the smoke reveals "
            "visions, but the future is erased forever. The Archive grows with every "
            "choice, its corridors stretching beyond reason, and those who read too "
            "many books begin to see their own face printed on blank pages."
        ),
    ),
    WorldCatalogItem(
        id="hollow-sea",
        title="The Hollow Sea",
        mode="Adventure",
        description=(
            "An ocean without water, filled with drifting ships and voices beneath the sand."
        ),
        image=(
            "linear-gradient(135deg, rgba(10,12,18,.3), rgba(0,0,0,.7)), "
            "url('./assets/world-hollow-sea.png')"
        ),
        tags=["Survival", "Black Sand", "Lost Ships"],
        world_seed=(
            "The Hollow Sea is an ocean without water: black sand, levitating "
            "shipwrecks, and voices rising from below. Answer them too often and "
            "they begin speaking in your future voice."
        ),
        long_description=(
            "The Hollow Sea is an ocean without water, only black sand, drifting "
            "shipwrecks, and voices rising from beneath the ground. The sand burns "
            "by day, freezes by night, and pulls down anyone foolish enough to walk "
            "barefoot. Ships from impossible eras hang above the dunes, held by a "
            "strange magnetic field. The voices below may belong to the dead, loved "
            "ones, or the traveler's future self. The last human refuge is the copper "
            "wreck called Song Hy, a welded city of smugglers, hunters, and people "
            "who harvest voices for profit."
        ),
    ),
)


def list_world_catalog() -> list[WorldCatalogItem]:
    return list(WORLD_CATALOG)


def get_world_catalog_item(world_id: str) -> WorldCatalogItem | None:
    return next((world for world in WORLD_CATALOG if world.id == world_id), None)
