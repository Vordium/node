# Vectors

`agent-ops-vectors-2c1c0679.json` covers four agent ops on the main network (genesis `2c1c0679`): `RegisterAgent`,
`RevokeAgent`, `SetAgentPolicy` and `SetAgentMarketLimit`. The file is kept unchanged because clients pin it.

- `RevokeAgent` and `SetAgentMarketLimit` are applied by the chain; their vectors are current.
- `RegisterAgent` (117) and `SetAgentPolicy` (119) are **no longer applied**: an op of these kinds changes nothing.
  Register an agent with `RegisterAgentV2` (129) and set its limits with `SetAgentPolicyV1` (132). Their EIP-712 types,
  fields and signing rules are in [docs/agents.md](../docs/agents.md) and in the `agents` section of
  <https://rpc.vordium.com/network-spec.json>.
