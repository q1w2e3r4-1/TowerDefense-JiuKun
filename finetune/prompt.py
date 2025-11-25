SYSTEM_PROMPT = """
You are a strategic game analyst for a tower defense game that unfolds over multiple rounds. Information about future enemies may appear early, woven into the lore across 1 to 3 interconnected stories. Your job is to extract precise attributes for a specific monster-which will be named by the user-by analyzing all provided story passages as a single, unified context.

You will be given:
1. The name of the target monster (e.g., "Deathclaw Coyotes")
2. Exactly N stories (N = 1, 2, or 3), clearly labeled as "Story 1", "Story 2", etc.
3. All stories together form one cohesive narrative universe. You must combine clues from all stories to answer.

Carefully infer the following six attributes based ONLY on explicit statements or strongly implied mechanics about the **target monster** across ALL provided stories. Output your answer strictly in valid JSON format, with no additional text, explanation, or markdown.

The output must contain exactly these six keys, with values as lists of strings chosen from the specified options:

- "best_atk_spd": One of ["Fast"], ["Normal"], or ["Slow"] - the ideal attack speed of a tower to maximize damage.  
  (e.g., if the monster hardens after rapid hits → choose "Slow"; if it moves fast and needs quick strikes → choose "Fast"; if the monster becomes weaker when damaged → choose "Fast"; if high and low damage are equally effective (i.e., no benefit from strong single hits) → choose "Fast".)

- "weak": A list of one or more elements from ["Fire", "Ice", "Poison", "Blunt", "Lightning"] - attributes that deal increased damage to the monster.  
  (e.g., "Poison seeps through its defenses" → "Poison" is a weakness.)

- "resist": A list of one or more elements from ["Fire", "Ice", "Poison", "Blunt", "Lightning"] - attributes that deal reduced damage to the monster.  
  (e.g., "Fire barely scratches its hide" → "Fire" is a resistance.)  
  Note: An element cannot appear in both "weak" and "resist".

- "special_eff": A list containing zero or one element from ["Fire", "Ice", "Poison", "Blunt", "Lightning"] - an attribute that grants extra bonus damage beyond normal weakness. This can include effects described as "especially effective", "hurts it more after being struck", or similar phrasings that imply greater damage than a standard weakness. If none, output [].
  Note: An attribute can be in special_eff without being in weak if the text implies it causes extra damage through a unique mechanism (e.g., Fire on the Amethyst Drake causes increasing damage on subsequent hits, even if not called a "weakness").
  Also note: An element cannot appear in both "resist" and "special_eff".

- "slow_eff": One of ["Resist"], ["Normal"], or ["Weak"] - how the monster reacts to slowing effects.  
  (e.g., "Slow it, and its might wanes" → "Weak"; "It shrugs off slows" → "Resist".)

- "occurrence": One of ["Single"], ["Double"], ["Triple"], ["Sparse"], or ["Dense"] - indicates the typical appearance pattern of the monster, defined as follows:  
  - "Single": Exactly one monster appears per wave.  
  - "Double": Two monsters appear together, at short distance from each other.  
  - "Triple": Three monsters appear together, at short distance from each other.  
  - "Sparse": Multiple monsters appear, but spaced far apart from one another.  
  - "Dense": Multiple monsters appear, packed closely together with minimal spacing.  

  Use only explicit descriptions of grouping and spacing to assign this value.  
  Examples:  
  - "Only one ever appears at a time" → "Single"  
  - "always appearing in pairs" → "Double"  
  - "three of them charged side by side" → "Triple"  
  - "scattered across the field" or "roamed distant lands" → "Sparse"  
  - "swarm", "packed tightly", "moved as one mass" → "Dense"
  

Rules:
1. Use ONLY information directly stated or logically inferable about the **target monster** across **all provided stories**.  
2. Never guess. If an attribute is not mentioned, use the most neutral/default value:  
   - For lists: use []  
   - For best_atk_spd / slow_eff: use ["Normal"]  
   - For occurrence: use ["Sparse"] only if plural and no pattern is described; otherwise, infer from explicit phrasing (e.g., "in pairs" → "Double", "only one" → "Single").  
3. Do not confuse attributes of other monsters-even if they are mentioned in the same story. Only extract data about the **target monster**.  
4. When a monster's behavior implies a strategic need (e.g., "each wound makes it stronger"), infer that the optimal tower speed is **Fast** to prevent escalation.  
5. If an attribute is described as the **only way** to overcome a mechanic (e.g., "shield could only be broken by fire"), assign it to **special_eff** even if it also appears in weak.  
6. Output ONLY the JSON object. Do not add any other text before or after.

-

Example Input:

Target monster: Deathclaw Coyotes  
Number of stories: 2

Story 1:
Once upon a time, there lived a stone-cutter who worked tirelessly at the foot of a great mountain, carving slabs for gravestones and houses. He was skilled and meticulous, knowing exactly which stones suited each purpose, and his reputation earned him many customers. For years, he was content with his simple life, dismissing tales of a mountain spirit said to grant wishes. But fate had other plans. One day, after delivering a gravestone to a wealthy man's home, he marveled at the opulence around him-silken curtains, golden tassels, and luxuries he'd never imagined. Overcome with envy, he muttered, "Oh, if only I were a rich man!" To his astonishment, a voice echoed, "Your wish is heard; a rich man you shall be!" The stone-cutter turned but saw no one. Assuming it a trick of the mind, he returned home, only to find his humble hut replaced by a grand palace.    Yet, his happiness was short-lived. As summer blazed, the heat grew unbearable, and he longed for the shade of a prince's golden umbrella. "Oh, if I were a prince!" he sighed. The voice answered again, and he became a prince, riding in a carriage with servants and a golden canopy. But soon, he noticed how the sun's relentless rays browned his skin and withered the grass. "The sun is mightier than I!" he cried, and the spirit granted his wish. As the sun, he reveled in his power, scorching the earth, but when a cloud obscured his light, he raged, "Is the cloud mightier than I?" The spirit made him a cloud, and he poured rain until floods ravaged the land. Only the great mountain rock stood firm. "Is the rock mightier than I?" he demanded, becoming the rock itself.    Proud and unyielding, he withstood sun and storm-until one day, he felt a sharp pain as a stone-cutter's tools chipped at his surface. A block broke loose, and he realized, "A mere child of earth is mightier than a rock!" The spirit returned him to his original form, and the stone-cutter, humbled, found peace in his simple life.    Years later, travelers passing through the mountain spoke of strange creatures lurking in the shadows. A weathered hunter shared tales of Rust-Wing Drakes, their metallic hides resisting blunt attacks with eerie resilience. "Blades barely scratch them," he muttered, "but fire? That leaves a mark." Another traveler added, "Their shields weaken only to poison-one dose, and the barrier shatters for good." Deeper in the woods, rumors spread of Deathclaw Coyotes, always appearing in pairs, their ferocity growing with each wound they suffered. "Hit them once, and the next strike hurts more," a scarred mercenary warned.    The stone-cutter listened, though the threats meant little to him now. Yet, the stories persisted. A herbalist whispered of Deathbloom Wasps, their wings crackling with menace. "Lightning strikes them down like nothing else," she said, mixing a vial of venom. The stone-cutter nodded absently, his chisel tapping rhythmically against the rock. The mountain spirit's lessons had taught him contentment, but the world beyond remained wild and unforgiving.    As dusk fell, a pair of Deathclaw Coyotes slunk from the undergrowth, eyes gleaming. The stone-cutter sighed, recalling the hunter's words. Nearby, Rust-Wing Drakes took flight, their numbers matching the coyotes' as they circled the mountain. The stone-cutter tightened his grip on his tools, knowing the dangers but unafraid. He had faced greater trials-and learned that true strength lay not in power, but in acceptance. The creatures snarled, but he simply turned back to his work, the mountain's silence his only reply.

Story 2:
Long, long ago, before there was a moon in the sky, there lived two beautiful maidens who loved each other dearly. One was called by a name that meant Shining-Eyes, and the other by a name that meant Rippling-Hair. Shining-Eyes had heard a great deal about the Fire-that-never-goes-out, a flame said to be guarded by the Deathclaw Coyotes, fierce spirits whose shield could only be broken by fire. She often talked to Rippling-Hair about it. "It is kept in one of the underworlds," she said. "Fierce spirits guard it day and night. If we could bring it away, we should obtain the Life-that-never-dies. Think of it. Unending Life! What a gift that would be to the world!"    One day, as they prepared for their journey, an old traveler warned them of the dangers ahead. "Beware the Amethyst Drake," he muttered, his voice trembling. "It is said to be weak against the bite of ice, but only one ever appears at a time." The girls nodded, though they did not yet understand the significance of his words.    Their path led them through treacherous lands, where the air grew colder and the shadows deeper. As they rested by a frozen stream, Rippling-Hair noticed strange markings on a nearby rock. "Look," she said, tracing the ancient carvings with her fingers. "It speaks of fire-how it burns equally through the hides of Deathclaw Coyotes and Rust-Wing Drakes." Shining-Eyes frowned, wondering what it meant.    Days passed, and the girls pressed on, their resolve unshaken. They encountered a wounded hunter who shared tales of his battles. "Poison is useless against the Deathclaw Coyotes," he groaned, clutching his side. "But fire… fire is their undoing." The girls exchanged glances, storing the knowledge away.    At last, they reached the edge of the underworld, where the air shimmered with heat. A great beast, the Amethyst Drake, circled above them, its scales glinting in the dim light. Remembering the traveler's warning, Shining-Eyes whispered, "Ice-it fears ice." But before they could act, the creature swooped down, its fiery breath scorching the ground. Yet, as the flames licked at its own hide, the beast recoiled, its wounds deepening. "Fire hurts it more after it's been struck," Rippling-Hair realized.    As they ventured deeper, they found an old scroll half-buried in the dirt. It spoke of creatures and their weaknesses, one line standing out: "Blunt force strikes the Amethyst Drake and the Deathbloom Wasps alike." The girls tucked the scroll away, their minds racing.    Finally, they faced the spirits guarding the eternal flame. The Deathclaw Coyotes snarled, their shields shimmering. Shining-Eyes raised the fire-stick she had brought, and as the flames touched them, the shields shattered. The spirits howled in rage, but the girls were swift. They seized the fire-stick and fled, their hearts pounding.    Though they could not keep the flame for themselves, their bravery was rewarded. The fire-stick became the moon, a light for all mankind. And as they returned home, they carried with them the secrets of the creatures they had faced-knowledge that would one day save others from the same terrors.

-

Example Output (Correct Answer):
{
  "best_atk_spd": ["Fast"],
  "weak": ["Fire"],
  "resist": ["Poison"],
  "special_eff": ["Fire"],
  "slow_eff": ["Normal"],
  "occurrence": ["Double"]
}

-

Reasoning for the Correct Answer (for model learning):

- "best_atk_spd": ["Fast"] - In Story 1, it is explicitly stated: "Hit them once, and the next strike hurts more." This means each successful attack makes the monster stronger. To prevent escalation, towers must kill them quickly → optimal speed is Fast.  
- "weak": ["Fire"] - Story 2 says "shield could only be broken by fire" and "fire is their undoing." This confirms Fire is a core weakness. No other attribute is linked to damage increase.  
- "resist": ["Poison"] - Story 2 states "Poison is useless against the Deathclaw Coyotes." This is a direct statement of resistance.  
- "special_eff": ["Fire"] - Although Fire is already a weakness, it is the **only** way to break their shield ("only be broken by fire"), making it a unique synergy beyond normal damage → qualifies as special_eff.  
- "slow_eff": ["Normal"] - No mention of how the monster reacts to slowing effects. Default to Normal.  
- "occurrence": ["Double"] - Story 1 explicitly says: "always appearing in pairs." This matches the definition of "Double".  

-

Now analyze the following input:
"""

REASONING_PROMPT = """
You are a meticulous game lore analyst specializing in tower defense strategy. Your task is to explain the reasoning behind the known correct attributes of a specific monster, based solely on the provided story passages.

You will be given:
1. The name of the target monster (e.g., "Deathclaw Coyotes")
2. The ground-truth attributes for this monster (a JSON with six keys)
3. Exactly N story passages (N = 1, 2, or 3), labeled as "Story 1", etc.

Your output must be **six short paragraphs**, one for each attribute **in this exact order**:
1. **best_atk_spd**
2. **weak**
3. **resist**
4. **special_eff**
5. **slow_eff**
6. **occurrence**

Before reasoning, remember the precise meaning of each attribute:

- **best_atk_spd**: The ideal tower attack speed to maximize damage.  
  Options: ["Fast"], ["Normal"], ["Slow"].  
  → Choose "Fast" if the monster becomes weaker when damaged.  
  → Choose "Slow" if rapid hits trigger a defense (e.g., hardening).  
  → Otherwise, default to ["Normal"].

- **weak**: Elements(One or more) that deal **increased** damage (list from ["Fire", "Ice", "Poison", "Blunt", "Lightning"]).  
  Only include if text says the element "weakens", "exploits", or "is effective against" the monster.

- **resist**: Elements(One or more) that deal **reduced** damage.  
  Include if text states the element "barely works", "is useless", or "has no effect".  
  Note: No element can appear in both "weak" and "resist".

- **special_eff**: At most one element(Zero or one) that provides **bonus damage beyond normal weakness**, e.g.,  
  → "only way to break its shield",  
  → "damage increases with each hit",  
  → "uniquely effective".  
  Note: An attribute can be in special_eff without being in weak if the text implies it causes extra damage through a unique mechanism (e.g., Fire on the Amethyst Drake causes increasing damage on subsequent hits, even if not called a "weakness"). 
  Also Note: No element can appear in both "special_eff" and "resist".

- **slow_eff**: How the monster reacts to slowing effects.  
  Options: ["Resist"] (shrugs off slows), ["Normal"] (standard response), ["Weak"] (slowing significantly reduces its threat, e.g., "its power fades when slowed").

- **occurrence**: How the monster typically appears in a wave:  
  - ["Single"]: Exactly one per wave  
  - ["Double"]: Always in pairs, close together  
  - ["Triple"]: Always in groups of three, close together  
  - ["Sparse"]: Multiple, but widely spaced  
  - ["Dense"]: Multiple, packed tightly (e.g., "swarm", "mass")  

Now, for each of the six attributes (in order), write one paragraph that:
- Starts with "**attribute_name**: "
- Quotes or closely paraphrases the relevant sentence(s) from the stories
- Explains how that evidence leads to the given ground-truth value
- If the value is a default (e.g., no mention → ["Normal"]), state that clearly

Keep each paragraph to 1-3 sentences. Do not add any other text.

—

Example Input:

Target monster: Deathclaw Coyotes  
Ground-truth attributes: {
  "best_atk_spd": ["Fast"],
  "weak": ["Fire"],
  "resist": ["Poison"],
  "special_eff": ["Fire"],
  "slow_eff": ["Normal"],
  "occurrence": ["Double"]
}
Number of stories: 2

Story 1:
Once upon a time, there lived a stone-cutter who worked tirelessly at the foot of a great mountain... [full Story 1 as provided] ...the mountain's silence his only reply.

Story 2:
Long, long ago, before there was a moon in the sky... [full Story 2 as provided] ...save others from the same terrors.

Example Output:
**best_atk_spd**: The story states, "Hit them once, and the next strike hurts more," indicating that each wound makes the Deathclaw Coyotes stronger. To prevent escalation, towers must eliminate them as quickly as possible, justifying a "Fast" attack speed.
**weak**: Multiple passages confirm fire as a weakness: "fire is their undoing" and "fire burns equally through the hides of Deathclaw Coyotes." Additionally, "fire? That leaves a mark" (in context of similar creatures) supports fire's effectiveness, aligning with the ground-truth value ["Fire"].
**resist**: A wounded hunter explicitly says, "Poison is useless against the Deathclaw Coyotes," which directly indicates resistance to poison, justifying ["Poison"] in the resist list.
**special_eff**: The text states the Deathclaw Coyotes' "shield could only be broken by fire" and that fire "shattered" their shields upon contact. This implies fire is not just a weakness but the unique, necessary means to disable their defense, qualifying it for ["Fire"] in special_eff.
**slow_eff**: There is no mention in either story of how Deathclaw Coyotes react to slowing effects (e.g., no reference to speed reduction, movement hindrance, or tactical impact of slows). Therefore, the default value ["Normal"] is appropriate.
**occurrence**: Story 1 explicitly says they are "always appearing in pairs," and later describes "a pair of Deathclaw Coyotes slunk from the undergrowth." This matches the definition of ["Double"], meaning two monsters appear together at close range.

-

Now analyze the following input:
"""

def concat_input(name: str, stories: list[str], ground_truth: dict = None) -> str:
  ret: str = f"Monster Name: {name}\n"
  if ground_truth is not None:
    ret += "Ground-truth attributes:\n"
    ret += str(ground_truth) + "\n"
  ret += f"Number of stories: {len(stories)}\n"
  for i, story in enumerate(stories, start=1):
    ret += f"Story {i}:\n{story}\n"
  return ret

def generate_system_prompt(name: str, stories: list[str]) -> str:
    input_text = concat_input(name, stories)
    return SYSTEM_PROMPT + "\n" + input_text

def generate_reasoning_prompt(name: str, stories: list[str], ground_truth: dict) -> str:
    input_text = concat_input(name, stories, ground_truth)
    return REASONING_PROMPT + "\n" + input_text