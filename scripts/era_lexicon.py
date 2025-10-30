"""
era_lexicon.py - Era-specific lexicons for Bollywood films

Provides common names, places, and terms for different Bollywood eras
to improve ASR/translation accuracy via context injection.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class EraLexicon:
    """Lexicon for a specific era"""
    era_name: str
    start_year: int
    end_year: int
    names: List[str]
    places: List[str]
    terms: List[str]


# Era-specific lexicons
ERA_LEXICONS = {
    "1950s-60s": EraLexicon(
        era_name="1950s-60s",
        start_year=1950,
        end_year=1969,
        names=[
            "Raj Kapoor", "Dilip Kumar", "Dev Anand", "Nargis", "Meena Kumari",
            "Waheeda Rehman", "Madhubala", "Rajendra Kumar", "Vyjayanthimala",
            "Shammi Kapoor", "Sadhana", "Shashi Kapoor"
        ],
        places=[
            "Bombay", "Calcutta", "Delhi", "Kashmir", "Shimla", "Agra", "Lucknow"
        ],
        terms=[
            "zamindaar", "sahib", "memsahib", "babu", "angrez", "raj", "maharaja"
        ]
    ),
    "1970s": EraLexicon(
        era_name="1970s",
        start_year=1970,
        end_year=1979,
        names=[
            "Amitabh Bachchan", "Dharmendra", "Rajesh Khanna", "Hema Malini",
            "Zeenat Aman", "Rekha", "Vinod Khanna", "Rishi Kapoor", "Neetu Singh",
            "Shashi Kapoor", "Jaya Bhaduri", "Parveen Babi"
        ],
        places=[
            "Bombay", "Mumbai", "Delhi", "Goa", "Kashmir", "Shimla", "Kolkata"
        ],
        terms=[
            "smuggler", "don", "police", "inspector", "thakur", "dacoit", "coolie"
        ]
    ),
    "1980s": EraLexicon(
        era_name="1980s",
        start_year=1980,
        end_year=1989,
        names=[
            "Amitabh Bachchan", "Anil Kapoor", "Jackie Shroff", "Sridevi",
            "Madhuri Dixit", "Jeetendra", "Mithun Chakraborty", "Rekha",
            "Jaya Prada", "Rishi Kapoor", "Sunny Deol", "Meenakshi Seshadri"
        ],
        places=[
            "Mumbai", "Delhi", "Goa", "Kashmir", "Ooty", "Bangalore", "Hyderabad"
        ],
        terms=[
            "don", "mafia", "businessman", "inspector", "commissioner", "dacoit"
        ]
    ),
    "1990s": EraLexicon(
        era_name="1990s",
        start_year=1990,
        end_year=1999,
        names=[
            "Shah Rukh Khan", "Salman Khan", "Aamir Khan", "Madhuri Dixit",
            "Kajol", "Juhi Chawla", "Karisma Kapoor", "Ajay Devgn", "Akshay Kumar",
            "Urmila Matondkar", "Sanjay Dutt", "Tabu", "Manisha Koirala"
        ],
        places=[
            "Mumbai", "Delhi", "Goa", "London", "Switzerland", "Simla", "Punjab"
        ],
        terms=[
            "NRI", "college", "romance", "family", "wedding", "business", "London"
        ]
    ),
    "2000s": EraLexicon(
        era_name="2000s",
        start_year=2000,
        end_year=2009,
        names=[
            "Shah Rukh Khan", "Hrithik Roshan", "Aamir Khan", "Salman Khan",
            "Kareena Kapoor", "Priyanka Chopra", "Preity Zinta", "Aishwarya Rai",
            "Abhishek Bachchan", "Saif Ali Khan", "Rani Mukerji", "Kajol"
        ],
        places=[
            "Mumbai", "Delhi", "New York", "London", "Punjab", "Goa", "Dubai"
        ],
        terms=[
            "NRI", "MBA", "CEO", "startup", "wedding", "sangeet", "Delhi belly"
        ]
    ),
    "2010s": EraLexicon(
        era_name="2010s",
        start_year=2010,
        end_year=2019,
        names=[
            "Ranveer Singh", "Ranbir Kapoor", "Deepika Padukone", "Alia Bhatt",
            "Katrina Kaif", "Anushka Sharma", "Varun Dhawan", "Shraddha Kapoor",
            "Ayushmann Khurrana", "Rajkummar Rao", "Kangana Ranaut", "Vidya Balan"
        ],
        places=[
            "Mumbai", "Delhi", "Gurgaon", "Bangalore", "London", "New York", "Dubai"
        ],
        terms=[
            "startup", "app", "social media", "wedding", "sangeet", "entrepreneur"
        ]
    ),
    "2020s": EraLexicon(
        era_name="2020s",
        start_year=2020,
        end_year=2029,
        names=[
            "Ranveer Singh", "Ranbir Kapoor", "Deepika Padukone", "Alia Bhatt",
            "Vicky Kaushal", "Kartik Aaryan", "Kiara Advani", "Janhvi Kapoor",
            "Sara Ali Khan", "Ananya Panday", "Siddhant Chaturvedi", "Tripti Dimri"
        ],
        places=[
            "Mumbai", "Delhi", "Gurgaon", "Bangalore", "Hyderabad", "Dubai", "London"
        ],
        terms=[
            "startup", "crypto", "influencer", "social media", "pandemic", "zoom"
        ]
    )
}


def get_era_lexicon(year: Optional[int]) -> Optional[EraLexicon]:
    """
    Get era lexicon for a given year

    Args:
        year: Movie release year

    Returns:
        EraLexicon or None if year not provided
    """
    if year is None:
        return None

    for era_key, lexicon in ERA_LEXICONS.items():
        if lexicon.start_year <= year <= lexicon.end_year:
            return lexicon

    # Default to closest era
    if year < 1950:
        return ERA_LEXICONS["1950s-60s"]
    elif year >= 2020:
        return ERA_LEXICONS["2020s"]

    return None


def get_era_terms(year: Optional[int]) -> List[str]:
    """
    Get combined list of all terms from era lexicon

    Args:
        year: Movie release year

    Returns:
        List of names, places, and terms
    """
    lexicon = get_era_lexicon(year)
    if not lexicon:
        return []

    return lexicon.names + lexicon.places + lexicon.terms


def format_era_context(year: Optional[int]) -> str:
    """
    Format era context as string for prompt injection

    Args:
        year: Movie release year

    Returns:
        Formatted string with era context
    """
    lexicon = get_era_lexicon(year)
    if not lexicon:
        return ""

    lines = [
        f"Era: {lexicon.era_name}",
        f"Notable names: {', '.join(lexicon.names[:8])}",
        f"Common places: {', '.join(lexicon.places[:6])}",
        f"Terms: {', '.join(lexicon.terms[:6])}"
    ]

    return "\n".join(lines)
