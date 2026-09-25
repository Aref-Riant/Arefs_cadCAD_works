# japanese_auction_cadcad.py

from cadCAD.configuration import Experiment
from cadCAD.configuration.utils import config_sim
from cadCAD.engine import ExecutionMode, ExecutionContext, Executor

import pandas as pd


# ============================================================
# 1. AUCTION PARAMETERS
# ============================================================

INITIAL_PRICE = 0
PRICE_INCREMENT = 5
MAX_STEPS = 100


# ============================================================
# 2. BIDDER DEFINITIONS
# ============================================================

BIDDERS = {
    "Alice": {
        "valuation": 100,
        "strategy": "truthful",
    },

    "Bob": {
        "valuation": 80,
        "strategy": "conservative",
    },

    "Charlie": {
        "valuation": 65,
        "strategy": "truthful",
    },

    "David": {
        "valuation": 50,
        "strategy": "aggressive",
    },
}


# ============================================================
# 3. BIDDER POLICY
# ============================================================

def bidder_policy(
    bidder,
    price,
    bidders,
):
    """
    Decide whether a bidder remains active at the given price.

    Returns:
        True  -> bidder stays
        False -> bidder exits permanently
    """

    bidder_data = bidders[bidder]

    valuation = bidder_data["valuation"]
    strategy = bidder_data["strategy"]

    # --------------------------------------------------------
    # Truthful strategy
    # --------------------------------------------------------

    if strategy == "truthful":

        # Stay while price is below valuation.
        return price < valuation

    # --------------------------------------------------------
    # Conservative strategy
    # --------------------------------------------------------

    elif strategy == "conservative":

        # Exit at 90% of private valuation.
        maximum_price = valuation * 0.90

        return price < maximum_price

    # --------------------------------------------------------
    # Aggressive strategy
    # --------------------------------------------------------

    elif strategy == "aggressive":

        # Willing to stay up to 110% of valuation.
        maximum_price = valuation * 1.10

        return price < maximum_price

    # --------------------------------------------------------
    # Unknown strategy
    # --------------------------------------------------------

    else:

        raise ValueError(
            f"Unknown strategy '{strategy}' "
            f"for bidder '{bidder}'"
        )


# ============================================================
# 4. AUCTION POLICY
# ============================================================

def auction_policy(
    params,
    substep,
    state_history,
    previous_state,
):
    """
    Main Japanese auction policy.

    The price increases each timestep.

    Active bidders decide whether to remain.

    IMPORTANT:
    Once the auction is finished, the current state is
    preserved and no further auction logic is executed.
    """

    # ========================================================
    # Freeze the terminal state.
    # ========================================================

    if previous_state["status"] == "finished":

        return {
            "next_price": previous_state["price"],
            "next_active_bidders": previous_state["active_bidders"],
            "winner": previous_state["winner"],
            "payment": previous_state["payment"],
            "status": "finished",
        }

    # ========================================================
    # Read current state
    # ========================================================

    current_price = previous_state["price"]

    active_bidders = previous_state["active_bidders"]

    bidders = params["bidders"]

    price_increment = params["price_increment"]

    # ========================================================
    # Increase price
    # ========================================================

    next_price = current_price + price_increment

    # ========================================================
    # Evaluate active bidders
    # ========================================================

    remaining_bidders = []

    for bidder in active_bidders:

        stays = bidder_policy(
            bidder=bidder,
            price=next_price,
            bidders=bidders,
        )

        if stays:

            remaining_bidders.append(bidder)

    # ========================================================
    # Determine auction outcome
    # ========================================================

    # --------------------------------------------------------
    # Exactly one bidder remains
    # --------------------------------------------------------

    if len(remaining_bidders) == 1:

        winner = remaining_bidders[0]

        return {
            "next_price": next_price,
            "next_active_bidders": remaining_bidders,
            "winner": winner,
            "payment": next_price,
            "status": "finished",
        }

    # --------------------------------------------------------
    # Nobody remains
    # --------------------------------------------------------

    elif len(remaining_bidders) == 0:

        return {
            "next_price": next_price,
            "next_active_bidders": [],
            "winner": None,
            "payment": None,
            "status": "finished",
        }

    # --------------------------------------------------------
    # Auction continues
    # --------------------------------------------------------

    else:

        return {
            "next_price": next_price,
            "next_active_bidders": remaining_bidders,
            "winner": None,
            "payment": None,
            "status": "running",
        }


# ============================================================
# 5. STATE UPDATE FUNCTIONS
# ============================================================

def update_price(
    params,
    substep,
    state_history,
    previous_state,
    policy_input,
):

    return (
        "price",
        policy_input["next_price"],
    )


def update_active_bidders(
    params,
    substep,
    state_history,
    previous_state,
    policy_input,
):

    return (
        "active_bidders",
        policy_input["next_active_bidders"],
    )


def update_winner(
    params,
    substep,
    state_history,
    previous_state,
    policy_input,
):

    return (
        "winner",
        policy_input["winner"],
    )


def update_payment(
    params,
    substep,
    state_history,
    previous_state,
    policy_input,
):

    return (
        "payment",
        policy_input["payment"],
    )


def update_status(
    params,
    substep,
    state_history,
    previous_state,
    policy_input,
):

    return (
        "status",
        policy_input["status"],
    )


# ============================================================
# 6. INITIAL STATE
# ============================================================

initial_state = {

    "price": INITIAL_PRICE,

    "active_bidders": list(BIDDERS.keys()),

    "winner": None,

    "payment": None,

    "status": "running",
}


# ============================================================
# 7. CADCAD PARTIAL STATE UPDATE BLOCK
# ============================================================

partial_state_update_blocks = [

    {

        "policies": {

            "auction": auction_policy,

        },

        "variables": {

            "price": update_price,

            "active_bidders": update_active_bidders,

            "winner": update_winner,

            "payment": update_payment,

            "status": update_status,

        },

    }

]


# ============================================================
# 8. SIMULATION PARAMETERS
# ============================================================

sim_params = {

    "bidders": [
        BIDDERS
    ],

    "price_increment": [
        PRICE_INCREMENT
    ],

}


# ============================================================
# 9. CADCAD CONFIGURATION
# ============================================================

simulation_config = config_sim(
    {

        # Number of Monte Carlo runs
        "N": 1,

        # Maximum number of timesteps
        "T": range(1, MAX_STEPS + 1),

        # Parameter values
        "M": sim_params,

    }
)


# ============================================================
# 10. CREATE EXPERIMENT
# ============================================================

experiment = Experiment()

experiment.append_configs(

    initial_state=initial_state,

    partial_state_update_blocks=partial_state_update_blocks,

    sim_configs=simulation_config,

)


# ============================================================
# 11. EXECUTE SIMULATION
# ============================================================

execution_context = ExecutionContext(
    context=ExecutionMode.single_proc
)


executor = Executor(

    exec_context=execution_context,

    configs=experiment.configs,

)


result = executor.execute()


# ============================================================
# 12. EXTRACT RESULTS
# ============================================================

records = result[0]

df = pd.DataFrame(records)


# ============================================================
# 13. DISPLAY AUCTION
# ============================================================

print()
print("=" * 110)
print("JAPANESE AUCTION")
print("=" * 110)
print()

print(
    f"{'Step':<8}"
    f"{'Price':<10}"
    f"{'Active bidders':<45}"
    f"{'Winner':<15}"
    f"{'Payment':<12}"
    f"{'Status'}"
)

print("-" * 110)


for _, row in df.iterrows():

    print(
        f"{str(row['substep']):<8}"
        f"{str(row['price']):<10}"
        f"{str(row['active_bidders']):<45}"
        f"{str(row['winner']):<15}"
        f"{str(row['payment']):<12}"
        f"{str(row['status'])}"
    )


# ============================================================
# 14. FIND FINAL AUCTION STATE
# ============================================================

# Because cadCAD keeps running timesteps after termination,
# the final dataframe row is not necessarily the moment at
# which the auction ended.
#
# So explicitly find the first finished state.

finished_rows = df[df["status"] == "finished"]


if len(finished_rows) > 0:

    final_state = finished_rows.iloc[0]

else:

    final_state = df.iloc[-1]


# ============================================================
# 15. DISPLAY FINAL RESULT
# ============================================================

print()
print("=" * 110)
print("FINAL RESULT")
print("=" * 110)

print(
    f"Winner  : {final_state['winner']}"
)

print(
    f"Payment : {final_state['payment']}"
)

print(
    f"Price   : {final_state['price']}"
)

print(
    f"Status  : {final_state['status']}"
)

print()
