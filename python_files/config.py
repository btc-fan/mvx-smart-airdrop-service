from multiversx_sdk import (
    AccountTransactionsFactory,
    AddressComputer,
    DelegationTransactionsFactory,
    RelayedTransactionsFactory,
    TokenManagementTransactionsFactory,
    TransactionComputer,
    TransactionsConverter,
    TransactionsFactoryConfig,
    TransferTransactionsFactory,
)
from multiversx_sdk.network_providers.proxy_network_provider import ProxyNetworkProvider

PROXY_PUBLIC_TESTNET = "https://testnet-gateway.multiversx.com"
PROXY_PUBLIC_DEVNET = "https://devnet-gateway.multiversx.com"
PROXY_DO_AMS = "http://188.166.13.136:8080"
PROXY_OVH_P03 = "http://51.89.62.133:8080"
PROXY_OVH_P04 = "http://51.89.62.131:8080"
PROXY_OVH_P06 = "http://51.89.16.187:8080"
PROXY_MVX_FRA = "http://49.51.171.106:8080"

PROXY_CHAIN_SIMULATOR = "http://localhost:8085"


# Change this for other network
PROXY_URL = PROXY_CHAIN_SIMULATOR
DEFAULT_PROXY = PROXY_CHAIN_SIMULATOR
# Get Chain ID
provider = ProxyNetworkProvider(PROXY_URL)
# CHAIN_ID = "1"  # Internal Test Network
CHAIN_ID = "chain"  # Chain Simulator
METACHAIN_ID = "4294967295"


# TEMP
OBSERVER_META = "http://localhost:55802"

try:
    proxy_default = ProxyNetworkProvider(DEFAULT_PROXY)
except:
    Exception

# config for cli flags for starting chain simulator
log_level = '"*:DEBUG,process:TRACE"'
num_validators_per_shard = "10"
num_validators_meta = "10"
num_waiting_validators_per_shard = "6"
num_waiting_validators_meta = "6"
# real config after staking v4 full activation: eligible = 10 *4 , waiting = (6-2) *4, qualified =  2*4
# qualified nodes from auction will stay in waiting 2 epochs

rounds_per_epoch = "50"

config = TransactionsFactoryConfig(CHAIN_ID)
transfer_transactions_factory = TransferTransactionsFactory(config)
account_transactions_factory = AccountTransactionsFactory(config)
delegation_transactions_factory = DelegationTransactionsFactory(config)
token_management_transaction_factory = TokenManagementTransactionsFactory(config)
factory = RelayedTransactionsFactory(config)
transaction_computer = TransactionComputer()
transaction_converter = TransactionsConverter
address_computer = AddressComputer()
