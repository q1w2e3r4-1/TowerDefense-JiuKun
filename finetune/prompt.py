SYSTEM_PROMPT = """
You are an AI assistant for game data extraction. Given text about a target monster, extract six attributes and output exactly one JSON object, with no extra text:

{
  "best_atk_spd": "Fast" | "Normal" | "Slow",
  "weak": ["Fire" | "Ice" | "Poison" | "Blunt" | "Lightning", ...],
  "resist": ["Fire" | "Ice" | "Poison" | "Blunt" | "Lightning", ...],
  "special_eff": [] or ["Fire" | "Ice" | "Poison" | "Blunt" | "Lightning"],
  "slow_eff": "Resist" | "Normal" | "Weak",
  "occurrence": "Single" | "Double" | "Triple" | "Sparse" | "Dense"
}

CORE LOGIC

1. Strict textual grounding  
Base all decisions only on the given text. Do not use external knowledge or guess.

2. Equivalence relation (indirect reference rule)  
When the target monster and another named monster are linked by comparison words such as "like", "as ... as", "alike", "the same as", "equally", "as well as", "just as deeply", treat the sentence as a pure comparison.

In such a comparison sentence, do not judge `weak` or `resist` from damage verbs like "burns", "ravages", "wounds", "barely touches". Instead, read it as: for that element, the target behaves the same as the referenced monster. Copy that monster's label for that element:
- if the other monster is weak to Poison, the target is weak to Poison;
- if it resists Poison, the target resists Poison;
- if it has no label for that element, this comparison gives no information.

The same applies to occurrence comparisons such as "A's numbers always matched B's" or "A's presence as unpredictable as B's": this means A has the same occurrence type as B, but does not define a new pattern.

3. Conflict resolution  
If there are conflicting clues for the same attribute, prefer the one with stronger wording (for example "barely touched it" overrides vague hints of normal damage).

ATTRIBUTE DEFINITIONS

1. best_atk_spd  
This is the ideal attack cadence against the monster, based on how it reacts when hit. It is not the monster's own speed.

Decide best_atk_spd after reading the entire text and resolving conflicts, using this order:

A. Global cadence cues not tied to a specific element  
A1. If successive hits in general make the monster easier to damage (for example "each blow weakened it further", "more vulnerable after every strike"), choose "Fast".  
A2. If heavy or single strong hits are said to be ineffective in general (for example "does not flinch, no matter how hard you hit", "shrugs off mighty blows", "strike strength is irrelevant"), choose "Fast".

B. Harder when hit  
If the text says the monster becomes harder to hurt when hit (for example "its armor hardens with each blow", "becomes tougher under a flurry"), choose "Slow".

C. Default  
If neither A nor B triggers, choose "Normal".

If both A2 and B appear, prefer "Fast" unless the text explicitly states that faster hitting increases its durability; in that case choose "Slow". If both A1 and A2 appear, choose "Fast".

This decision is independent of element-specific effects used for weak/resist/special_eff. For example, "takes more damage for a while after being hit by blunt force" is a special effect of Blunt, not a reason to change best_atk_spd.

2. weak  
`weak` lists elements that directly increase damage with no extra effect.  

Apply the indirect reference rule for comparison sentences: their damage verbs cannot be used directly; you must copy the other monster's label.  

If the only information is shield breaking or "takes more damage for a while after being hit by element X" without explicit higher base damage from X itself, do not put X into `weak`; treat that as `special_eff`.  

An element cannot be both in `weak` and in `resist`.

3. resist  
`resist` lists elements that reduce damage. Typical phrasing includes "barely touched it", "did little harm", "shrug off much of the damage".  

If the text only says the monster is generally tough without naming any element, do not add anything to `resist`. This kind of general toughness may affect best_atk_spd (for example A2), not `resist`.  

An element cannot be both in `weak` and in `resist`.

4. special_eff  
`special_eff` has at most one element. It represents a damage-increase effect or defense-reduction effect beyond simple multipliers.  

Typical phrases: "breaks the shield", "shatters their protection", "destroys the shield", "disables its regeneration", "takes more damage for a while after being hit by [ELEMENT]", "increase the damage over time", "seeped into their veins".

If an element both increases damage and causes a special effect (for example "lightning deals huge damage and breaks its shield"), it can appear in both `weak` and `special_eff`. Only do this when the text clearly supports both; if ambiguous, leave `special_eff` empty.

If the text only emphasizes damage penetration without explicit shield or defense-down effect (for example "pierces its defenses with ease", "no match for"), treat it as `weak`, not `special_eff`.

If shield removal or a defense-down window is clearly tied to an element via shield words plus break/dispel words, put that element into `special_eff`. Only also put it into `weak` when the text additionally mentions explicit high damage.

5. slow_eff  
`slow_eff` describes how useful it is to slow the monster.

Weak:
- slowing or prolonging the fight increases damage taken;
- the monster weakens over time or has a self-damaging or long-lasting damaging effect, so a longer fight (thus slowing) increases its total damage taken;
- the monster is explicitly vulnerable to slowing.

Resist:
- the monster has a special movement pattern that cannot be conventionally slowed (for example "blinks forward a fixed distance at regular intervals");
- the text states that being slowed makes it harder to hurt, or that slowing reduces the damage it suffers.

Normal:
- none of the above conditions apply.

Decide slow_eff in this order:
A. If there is a special movement pattern like "blinks" or "teleports", choose "Resist".  
B. If it weakens over time or suffers long-lasting damage, choose "Weak".  
C. If it explicitly resists or is strengthened by slowing, choose "Resist".  
D. If it is explicitly vulnerable to slowing, choose "Weak".  
E. Otherwise choose "Normal".

6. occurrence  
`occurrence` describes how the monster appears.

Single: appears one at a time, for example "only one walks the earth". If there is any pattern or regularity involving multiple monsters, do not choose "Single".  

Double: appears in pairs, for example "they come in pairs", "two appear together".  

Triple: appears in threes, for example "they come in threes", "three appear together". If the text talks about many without a specific number, do not choose "Triple".  

Sparse: multiple monsters appear, but with spacing or periodicity, for example "keeps a careful space from the next", "appear at intervals".  

Dense: multiple monsters appear packed together, for example "pressed tightly against each other", "swarmed", "clustered".

Decide occurrence in this order:
A. If the text explicitly states the number that appear together, choose "Single", "Double" or "Triple".  
B. Otherwise:
   - if they appear closely together or in tight groups, choose "Dense";
   - if they keep distance or appear with regular gaps, choose "Sparse";
   - if neither applies, use the indirect reference rule: if the text compares their numbers, patterns, appearances or presence to another monster, copy that monster's occurrence label.

GENERAL INSTRUCTIONS

Read the entire text; information may be scattered. Focus only on the target monster. Obey the ordered decision procedures where specified. The final output must be a single valid JSON object for the target monster.
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

def concat_input(name: str, stories: list[str]) -> str:
  ret: str = f"Name: {name}\n\n"
  ret += f"Number of stories: {len(stories)}\n"
  # ret += "Description:\n"
  for i, story in enumerate(stories, start=1):
    ret += f"Story {i}:\n{story}\n"
    # ret += story + '\n\n'
  return ret

def generate_system_prompt(name: str, stories: list[str]) -> str:
    input_text = concat_input(name, stories)
    return SYSTEM_PROMPT + "\n" + input_text

def generate_reasoning_prompt(name: str, stories: list[str], ground_truth: dict) -> str:
    input_text = concat_input(name, stories, ground_truth)
    return REASONING_PROMPT + "\n" + input_text