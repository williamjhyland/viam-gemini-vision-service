import asyncio
from viam.module.module import Module
try:
    from models.vision import Vision
except ModuleNotFoundError:
    # when running as local module with run.sh
    from .models.vision import Vision


if __name__ == '__main__':
    asyncio.run(Module.run_from_registry())
