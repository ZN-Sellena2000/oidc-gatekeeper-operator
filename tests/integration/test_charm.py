# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

from pathlib import Path

import pytest
import yaml
from pytest_operator.plugin import OpsTest

METADATA = yaml.safe_load(Path("./metadata.yaml").read_text())
APP_NAME = METADATA["name"]
OIDC_CONFIG = {
    "client-name": "Ambassador Auth OIDC",
    "client-secret": "oidc-client-secret",
}
ISTIO_PILOT = "istio-pilot"
KEYCLOAK = "keycloak"


@pytest.mark.abort_on_fail
async def test_build_and_deploy(ops_test: OpsTest):
    """Build and deploy the charm.

    Assert on the unit status.
    """
    charm_under_test = await ops_test.build_charm(".")
    image_path = METADATA["resources"]["oci-image"]["upstream-source"]
    resources = {"oci-image": image_path}

    await ops_test.model.deploy(
        charm_under_test, resources=resources, trust=True, config=OIDC_CONFIG
    )
    await ops_test.model.wait_for_idle(
        apps=[APP_NAME], status="active", raise_on_blocked=True, timeout=60 * 10
    )
    assert ops_test.model.applications[APP_NAME].units[0].workload_status == "active"


@pytest.mark.abort_on_fail
async def test_relations(ops_test: OpsTest):
    await ops_test.model.deploy(ISTIO_PILOT, channel="1.5/stable")
    await ops_test.model.deploy(KEYCLOAK, channel="latest/edge", trust=True)
    await ops_test.model.add_relation(ISTIO_PILOT, KEYCLOAK)
    await ops_test.model.add_relation(f"{ISTIO_PILOT}:ingress", f"{APP_NAME}:ingress")
    await ops_test.model.add_relation(f"{ISTIO_PILOT}:ingress-auth", f"{APP_NAME}:ingress-auth")

    await ops_test.model.wait_for_idle(
        [APP_NAME, ISTIO_PILOT, KEYCLOAK],
        status="active",
        raise_on_blocked=True,
        raise_on_error=True,
        timeout=600,
    )


async def test_update_public_url(ops_test: OpsTest):
    public_url = "test-url"
    await ops_test.model.applications[KEYCLOAK].set_config({"public-url": public_url})
    await ops_test.model.applications[APP_NAME].set_config({"public-url": public_url})

    await ops_test.model.wait_for_idle(
        [APP_NAME, KEYCLOAK],
        status="active",
        raise_on_blocked=True,
        raise_on_error=True,
        timeout=600,
    )
