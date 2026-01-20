"""Test data for performance testing."""

import random

# Sample claims for invalidity search
INVALIDITY_CLAIMS = [
    """A method for monitoring tire pressure in a vehicle, comprising:
    mounting a pressure sensor on each tire;
    wirelessly transmitting pressure data to a central receiver;
    displaying the pressure information on a dashboard display.""",

    """An apparatus for wheel hub bearing assembly, comprising:
    an outer ring with an inner raceway;
    an inner ring with an outer raceway;
    rolling elements disposed between the raceways;
    a seal assembly to prevent contaminant ingress.""",

    """A system for vehicle suspension control, comprising:
    multiple shock absorbers connected to vehicle wheels;
    sensors for detecting road surface conditions;
    an electronic control unit for adjusting damping force;
    actuators for modifying suspension characteristics in real-time.""",

    """A brake pad composition comprising:
    a friction material with ceramic particles;
    a metal backing plate;
    an adhesive layer bonding the friction material to the backing plate;
    wherein the ceramic particles provide improved heat resistance.""",

    """A method for steering control in an electric vehicle, comprising:
    receiving steering input from a driver;
    processing the input through an electronic control module;
    actuating an electric motor to adjust wheel angle;
    providing haptic feedback to the driver through the steering wheel.""",
]

# Sample claims for infringement search
INFRINGEMENT_CLAIMS = [
    """1. A tire pressure monitoring system comprising:
    a plurality of pressure sensors, each mounted within a tire;
    a wireless transmitter associated with each sensor;
    a central processing unit receiving transmitted pressure data;
    a display unit showing real-time pressure readings.""",

    """1. A wheel bearing assembly comprising:
    a first raceway formed on an outer race component;
    a second raceway formed on an inner race component;
    a plurality of rolling elements between said raceways;
    a magnetic encoder for rotational speed sensing.""",

    """1. An active suspension system for a motor vehicle, the system comprising:
    at least one adaptive shock absorber per wheel;
    acceleration sensors detecting vertical wheel movement;
    a microprocessor controlling damping characteristics;
    hydraulic actuators for real-time adjustment.""",

    """1. A friction material for vehicle brakes comprising:
    a matrix of phenolic resin;
    reinforcing fibers distributed throughout the matrix;
    metallic particles for thermal conductivity;
    wherein said material exhibits a coefficient of friction between 0.35 and 0.45.""",

    """1. An electric power steering system comprising:
    a torque sensor on the steering column;
    an electric assist motor;
    an electronic control unit receiving torque sensor signals;
    wherein said control unit determines motor assist based on vehicle speed and torque input.""",
]

# Sample invention descriptions for patentability search
PATENTABILITY_DESCRIPTIONS = [
    """An innovative tire pressure monitoring system that uses artificial intelligence
    to predict tire failures before they occur. The system combines pressure sensors
    with temperature sensors and uses machine learning algorithms to analyze patterns
    and predict potential issues, alerting drivers proactively.""",

    """A novel wheel bearing design incorporating self-lubricating materials that
    eliminate the need for grease replenishment throughout the vehicle's lifetime.
    The bearing uses advanced ceramic-polymer composites that release lubricant
    gradually during operation.""",

    """An adaptive suspension system that uses LIDAR sensors to scan the road ahead
    and preemptively adjust suspension settings before encountering obstacles.
    This predictive approach significantly improves ride comfort and vehicle handling.""",

    """A brake system with integrated energy recovery that captures kinetic energy
    during braking and stores it in a supercapacitor for later use. The system
    includes a novel friction material that maintains consistent performance
    across a wide temperature range.""",

    """A steer-by-wire system with redundant electronic pathways and mechanical
    backup for fail-safe operation. The system includes artificial intelligence
    that can detect driver fatigue and make subtle steering corrections to
    maintain lane position.""",
]

# Sample patent document numbers
PATENT_NUMBERS = [
    "US20200001234A1",
    "US20200005678A1",
    "US20190012345A1",
    "US20190098765A1",
    "US20180054321A1",
    "US20180067890A1",
    "US20170011111A1",
    "US20170022222A1",
    "US20160033333A1",
    "US20160044444A1",
]

# Classification prefixes
CLASSIFICATIONS = [
    "B60B",
    "B60C",
    "B60G",
    "B60T",
    "B62D",
    "F16C",
    "F16D",
    "",  # No filter
]

# Keywords
KEYWORDS_SETS = [
    "tire, pressure, monitoring",
    "wheel, bearing, hub",
    "suspension, damper, shock",
    "brake, friction, pad",
    "steering, electric, motor",
    "",  # No keywords
]


def get_random_invalidity_query():
    """Get random invalidity search query data."""
    return {
        "query_claims": random.choice(INVALIDITY_CLAIMS),
        "doc_number": "",
        "target_date": f"20{random.randint(15, 23)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
        "classification_prefix": random.choice(CLASSIFICATIONS),
        "keywords": random.choice(KEYWORDS_SETS),
        "title_search": "",
        "top_k": random.choice([10, 15, 20, 25]),
    }


def get_random_infringement_query():
    """Get random infringement search query data."""
    return {
        "my_claims": random.choice(INFRINGEMENT_CLAIMS),
        "my_doc_number": "",
        "date_from": f"20{random.randint(10, 18)}-01-01",
        "date_to": f"20{random.randint(20, 24)}-12-31",
        "min_similarity": round(random.uniform(0.3, 0.7), 2),
        "classification_prefix": random.choice(CLASSIFICATIONS),
        "keywords": random.choice(KEYWORDS_SETS),
        "title_search": "",
        "top_k": random.choice([10, 15, 20, 25]),
    }


def get_random_patentability_query():
    """Get random patentability search query data."""
    return {
        "invention_description": random.choice(PATENTABILITY_DESCRIPTIONS),
        "draft_claims": "",
        "classification_prefix": random.choice(CLASSIFICATIONS),
        "keywords": random.choice(KEYWORDS_SETS),
        "title_search": "",
        "top_k": random.choice([10, 15, 20, 25]),
    }


def get_random_history_entry():
    """Get random search history entry data."""
    scenario = random.choice(["invalidity", "infringement", "patentability"])

    if scenario == "invalidity":
        query_data = {
            "queryClaims": random.choice(INVALIDITY_CLAIMS)[:200],
            "queryDocNumber": "",
            "targetDate": "",
            "patentNumber": "",
        }
    elif scenario == "infringement":
        query_data = {
            "myClaims": random.choice(INFRINGEMENT_CLAIMS)[:200],
            "myDocNumber": "",
            "dateFrom": "",
            "dateTo": "",
            "minSimilarity": 0.5,
            "patentNumber": "",
        }
    else:
        query_data = {
            "inventionDescription": random.choice(PATENTABILITY_DESCRIPTIONS)[:200],
            "draftClaims": "",
            "patentNumber": "",
        }

    return {
        "scenario": scenario,
        "query_data": query_data,
        "result_count": random.randint(5, 25),
        "search_time_ms": round(random.uniform(100, 2000), 2),
    }
