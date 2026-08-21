"""Stage 0: Contract validation — OpenAPI specs parse and refs resolve."""
import pathlib

import pytest
import yaml

CONTRACTS_DIR = pathlib.Path(__file__).resolve().parents[2] / "contracts" / "openapi"


def _load_specs():
    if not CONTRACTS_DIR.exists():
        pytest.skip("No contracts/openapi/ directory")
    specs = list(CONTRACTS_DIR.glob("*.yaml")) + list(CONTRACTS_DIR.glob("*.yml"))
    if not specs:
        pytest.skip("No OpenAPI specs found")
    return specs


@pytest.fixture(params=[s.name for s in _load_specs()] if CONTRACTS_DIR.exists() else [])
def spec_path(request):
    return CONTRACTS_DIR / request.param


@pytest.fixture
def spec(spec_path):
    return yaml.safe_load(spec_path.read_text())


class TestOpenAPIContractValidation:

    @pytest.fixture(autouse=True)
    def _specs(self):
        self.specs = _load_specs()

    @pytest.mark.parametrize("spec_file", [s.name for s in _load_specs()] if CONTRACTS_DIR.exists() else [])
    def test_spec_parses(self, spec_file):
        spec = yaml.safe_load((CONTRACTS_DIR / spec_file).read_text())
        assert "openapi" in spec or "swagger" in spec, f"{spec_file} missing openapi version"

    @pytest.mark.parametrize("spec_file", [s.name for s in _load_specs()] if CONTRACTS_DIR.exists() else [])
    def test_spec_has_info(self, spec_file):
        spec = yaml.safe_load((CONTRACTS_DIR / spec_file).read_text())
        assert "info" in spec, f"{spec_file} missing info block"
        assert "title" in spec["info"], f"{spec_file} missing info.title"

    @pytest.mark.parametrize("spec_file", [s.name for s in _load_specs()] if CONTRACTS_DIR.exists() else [])
    def test_spec_has_paths(self, spec_file):
        spec = yaml.safe_load((CONTRACTS_DIR / spec_file).read_text())
        assert "paths" in spec, f"{spec_file} missing paths"
        assert len(spec["paths"]) > 0, f"{spec_file} has no path definitions"

    @pytest.mark.parametrize("spec_file", [s.name for s in _load_specs()] if CONTRACTS_DIR.exists() else [])
    def test_all_operations_have_responses(self, spec_file):
        spec = yaml.safe_load((CONTRACTS_DIR / spec_file).read_text())
        for path, methods in spec.get("paths", {}).items():
            for method, operation in methods.items():
                if method.startswith("x-") or method == "parameters":
                    continue
                assert "responses" in operation, (
                    f"{spec_file}: {method.upper()} {path} missing responses"
                )

    @pytest.mark.parametrize("spec_file", [s.name for s in _load_specs()] if CONTRACTS_DIR.exists() else [])
    def test_schema_refs_resolve(self, spec_file):
        text = (CONTRACTS_DIR / spec_file).read_text()
        spec = yaml.safe_load(text)
        components = spec.get("components", {}).get("schemas", {})

        def _find_refs(obj, path=""):
            if isinstance(obj, dict):
                if "$ref" in obj:
                    ref = obj["$ref"]
                    if ref.startswith("#/components/schemas/"):
                        schema_name = ref.split("/")[-1]
                        assert schema_name in components, (
                            f"{spec_file}: unresolved $ref {ref} at {path}"
                        )
                for k, v in obj.items():
                    _find_refs(v, f"{path}.{k}")
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    _find_refs(item, f"{path}[{i}]")

        _find_refs(spec)
