from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/release-images.yaml"


def test_release_pipeline_publishes_both_immutable_amd64_images():
    source = WORKFLOW.read_text()

    assert "publish-runtime:" in source
    assert "publish-presentation:" in source
    assert "platforms: linux/amd64" in source
    assert "multi-agent-quickstart" in source
    assert "operate-agentic-blueprint-presentation" in source
    assert "type=sha,format=long" in source


def test_release_pipeline_emits_provenance_sbom_signatures_and_source_labels():
    source = WORKFLOW.read_text()

    assert source.count("provenance: mode=max") == 2
    assert source.count("sbom: true") == 2
    assert source.count("cosign sign --yes") == 2
    assert source.count("actions/attest-build-provenance@v2") == 2
    assert source.count("org.opencontainers.image.source=") == 2
    assert source.count("org.opencontainers.image.revision=") == 2
    assert "packages: write" in source
    assert "id-token: write" in source
    assert "attestations: write" in source


def test_release_pipeline_tests_before_any_publish_job():
    source = WORKFLOW.read_text()

    assert "needs: test" in source
    assert "pytest tests/contracts/ tests/unit/ tests/publication/ -q" in source
    assert "npm run test" in source
    assert "npm run verify:offline" in source
