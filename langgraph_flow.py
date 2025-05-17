# langgraph_flow.py

from langgraph.graph import StateGraph, END
from typing import TypedDict
from langchain_core.runnables import RunnableLambda
from email_parser import parse_email
from aircraft_matcher import load_aircraft_data, match_aircrafts
from rule_filter import apply_nl_rule
from routing_agent import enrich_with_routing_info
from weather_agent import check_weather_for_trip
from reposition_agent import suggest_repositioning
from openai import OpenAI
import json
import os

class TripState(TypedDict):
    email: str
    parsed_trip: dict
    matched_aircrafts: list
    final_aircrafts: list
    rule: str
    explanation: str
    weather: dict
    route: str
    reposition_suggestions: dict

def get_weather(location: str) -> dict:
    return check_weather_for_trip({"origin": location, "destination": location})

def get_reposition_suggestions(origin: str) -> dict:
    return suggest_repositioning({"origin": origin})

def tool_calling_router_node(state: TripState) -> TripState:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    prompt = f"""
You are a routing assistant for an aviation trip matcher app.

Decide which tool to use for this trip info: {state['parsed_trip']}
and user rule: {state.get('rule', '')}

Only call one of the tools below and provide required parameters.
"""

    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get live weather conditions",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string"}
                    },
                    "required": ["location"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_reposition_suggestions",
                "description": "Get repositioning demand suggestions",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "origin": {"type": "string"}
                    },
                    "required": ["origin"]
                }
            }
        }
    ]

    response = client.chat.completions.create(
        model="gpt-4-0613",
        messages=[{"role": "system", "content": prompt}],
        tools=tools,
        tool_choice="required"
    )

    tool_call = response.choices[0].message.tool_calls[0]
    return {**state, "route": tool_call.function.name}

def parse_email_node(state: TripState) -> TripState:
    parsed = parse_email(state["email"])
    return {**state, "parsed_trip": parsed}

def match_aircraft_node(state: TripState) -> TripState:
    aircrafts = load_aircraft_data()
    matched = match_aircrafts(state["parsed_trip"], aircrafts)
    return {**state, "matched_aircrafts": matched}

def enrich_routing_node(state: TripState) -> TripState:
    enriched = enrich_with_routing_info(state["parsed_trip"], state["matched_aircrafts"])
    return {**state, "matched_aircrafts": enriched}

def weather_check_node(state: TripState) -> TripState:
    origin = state["parsed_trip"].get("origin", "")
    weather = get_weather(origin)
    return {**state, "weather": weather}

def reposition_agent_node(state: TripState) -> TripState:
    origin = state["parsed_trip"].get("origin", "")
    suggestions = get_reposition_suggestions(origin)
    return {**state, "reposition_suggestions": suggestions}

def apply_rule_node(state: TripState) -> TripState:
    aircrafts = state.get("matched_aircrafts", [])
    rule = state.get("rule", "").strip()
    weather = state.get("weather", {})

    context_prompt = f"""
Aircraft candidates:
{json.dumps(aircrafts, indent=2)}

Weather at origin: {weather.get('origin_weather')}
Weather at destination: {weather.get('destination_weather')}
Safe to fly based on wind: {weather.get('safe_to_fly', 'Unknown')}

User rule: "{rule}"
"""

    try:
        filtered = apply_nl_rule(rule, aircrafts, extra_context=context_prompt) if rule else aircrafts
        if not filtered:
            return {
                **state,
                "final_aircrafts": aircrafts,
                "rule_applied": bool(rule),
                "rule_warning": "Rule returned no matches. Showing all available aircraft."
            }
        return {**state, "final_aircrafts": filtered, "rule_applied": bool(rule)}
    except Exception:
        return {
            **state,
            "final_aircrafts": [{"error": "Failed to apply rule. Try rephrasing."}],
            "rule_applied": False
        }

def explain_matches_node(state: TripState) -> TripState:
    aircraft = state["final_aircrafts"]
    trip = state["parsed_trip"]
    if not aircraft or "error" in aircraft[0]:
        return {**state, "explanation": "No matches to explain.", "route": state.get("route")}

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    prompt = f"""
You are an aviation assistant. The user requested a trip: {trip}

These aircraft were selected:
{json.dumps(aircraft, indent=2)}

In 1–2 sentences, explain why these were good matches.
"""
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    explanation = response.choices[0].message.content.strip()
    return {**state, "explanation": explanation}

def routing_condition(state: TripState) -> str:
    return state.get("route", "get_weather")

builder = StateGraph(TripState)
builder.add_node("parse_email", RunnableLambda(parse_email_node))
builder.add_node("match_aircraft", RunnableLambda(match_aircraft_node))
builder.add_node("enrich_routing", RunnableLambda(enrich_routing_node))
builder.add_node("tool_router", RunnableLambda(tool_calling_router_node))
builder.add_node("weather_check", RunnableLambda(weather_check_node))
builder.add_node("reposition_agent", RunnableLambda(reposition_agent_node))
builder.add_node("apply_rule", RunnableLambda(apply_rule_node))
builder.add_node("explain_matches", RunnableLambda(explain_matches_node))

builder.set_entry_point("parse_email")
builder.add_edge("parse_email", "match_aircraft")
builder.add_edge("match_aircraft", "enrich_routing")
builder.add_edge("enrich_routing", "tool_router")
builder.add_conditional_edges("tool_router", routing_condition, {
    "get_weather": "weather_check",
    "get_reposition_suggestions": "reposition_agent"
})
builder.add_edge("weather_check", "apply_rule")
builder.add_edge("reposition_agent", "apply_rule")
builder.add_edge("apply_rule", "explain_matches")
builder.add_edge("explain_matches", END)

graph = builder.compile()



# --- Graph visualization ---
def get_graph_figure():
    import networkx as nx
    import matplotlib.pyplot as plt
    G = nx.DiGraph()
    G.add_edges_from([
        ("parse_email", "match_aircraft"),
        ("match_aircraft", "enrich_routing"),
        ("enrich_routing", "tool_router"),
        ("tool_router", "weather_check"),
        ("tool_router", "reposition_agent"),
        ("weather_check", "apply_rule"),
        ("reposition_agent", "apply_rule"),
        ("apply_rule", "explain_matches"),
        ("explain_matches", "END"),
    ])
    pos = nx.spring_layout(G)
    fig, ax = plt.subplots()
    nx.draw_networkx(G, pos, with_labels=True, node_color='lightblue', edge_color='gray', ax=ax)
    ax.set_title("LangGraph Workflow (Tool Calling)")
    ax.axis("off")
    return fig