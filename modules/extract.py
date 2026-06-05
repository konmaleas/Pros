from path_manipulation import dst_exists
from os.path import join, exists
from os import listdir
from dataclasses import dataclass
import py7zr as z7
import zipfile


@dataclass
class Paths:
    first_path: str
    second_path: str


@dataclass
class Zip(Paths):
    file: str

    def extract(self):
        if self.file.endswith('.zip'):
            self.zip_()
        elif self.file.endswith('.7z'):
            self.z7_()

    def compress(self):
        try:
            with zipfile.ZipFile(join(self.first_path, 'test.zip'), mode='a', compression=zipfile.ZIP_LZMA) as archive:
                archive.write(join(self.first_path, self.file))
        except FileNotFoundError as FNFE:
            print(FNFE)
        except zipfile.BadZipFile as BZF:
            print(BZF)

    def z7_(self):
        try:
            with z7.SevenZipFile(join(self.first_path, self.file), 'r') as archive:
                archive.extractall(dst_exists(self.second_path))
                if exists(join(self.second_path, self.file)):
                    print(f'File {self.second_path} just uncompressed')
        except FileNotFoundError:
            print(FileNotFoundError)
        except z7.exceptions.Bad7zFile:
            print(z7.exceptions.Bad7zFile)

    def zip_(self):
        try:
            zip_archive = zipfile.ZipFile
            with zip_archive(join(self.first_path, self.file), 'r') as archive:
                archive.extractall(dst_exists(self.second_path))
                if exists(self.second_path):
                    print(f'File {self.second_path} just uncompressed')
        except FileNotFoundError as FNFE:
            print(FNFE)
        except zipfile.BadZipFile as BZF:
            print(BZF)


def main():
    compressed_file = Zip('/home/konstantinos/Documents/PyTests/Submission Process/2211 au/dst/20230616/unzipped',
                            '', '')
    for e, ld in enumerate(listdir(compressed_file.first_path)):
        compressed_file.file = ld
        print(e, compressed_file)
        # compressed_file.extract()
        compressed_file.compress()
