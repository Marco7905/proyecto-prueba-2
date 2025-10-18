import shutil
import tempfile
import unittest
from pathlib import Path

try:
    from PIL import Image
except ModuleNotFoundError:  # pragma: no cover - entorno sin Pillow
    Image = None  # type: ignore[assignment]

from reduce_image import ResizeOptions, reduce_image_in_place


@unittest.skipUnless(Image is not None, "Pillow no está disponible en el entorno de pruebas")
class ReduceImageInPlaceTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = Path(tempfile.mkdtemp(prefix="reduce-image-tests-"))

    def tearDown(self) -> None:
        shutil.rmtree(self._tmpdir)

    def _create_image(self, name: str, size: tuple[int, int]) -> Path:
        path = self._tmpdir / name
        Image.new("RGB", size, color=(255, 0, 0)).save(path)
        return path

    def test_width_greater_than_original_does_not_enlarge(self) -> None:
        image_path = self._create_image("original.jpg", (120, 60))

        changed = reduce_image_in_place(image_path, ResizeOptions(width=1000))

        self.assertFalse(changed)
        with Image.open(image_path) as image:
            self.assertEqual(image.size, (120, 60))

    def test_width_reduction_preserves_aspect_ratio(self) -> None:
        image_path = self._create_image("width.jpg", (200, 100))

        changed = reduce_image_in_place(image_path, ResizeOptions(width=80))

        self.assertTrue(changed)
        with Image.open(image_path) as image:
            self.assertEqual(image.size, (80, 40))

    def test_height_reduction_preserves_aspect_ratio(self) -> None:
        image_path = self._create_image("height.jpg", (160, 90))

        changed = reduce_image_in_place(image_path, ResizeOptions(height=45))

        self.assertTrue(changed)
        with Image.open(image_path) as image:
            self.assertEqual(image.size, (80, 45))

    def test_both_dimensions_are_treated_as_maximums(self) -> None:
        image_path = self._create_image("limits.jpg", (300, 200))

        changed = reduce_image_in_place(image_path, ResizeOptions(width=600, height=150))

        self.assertTrue(changed)
        with Image.open(image_path) as image:
            self.assertEqual(image.size, (225, 150))


if __name__ == "__main__":
    unittest.main()
