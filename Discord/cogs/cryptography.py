
import discord
from discord.ext import commands

import hashlib
from typing import Literal
import zlib

from cryptography.hazmat.backends.openssl import backend as openssl_backend
from cryptography.hazmat.primitives import hashes as crypto_hashes
# import pygost.gost28147
# import pygost.gost28147_mac
# import pygost.gost34112012
# import pygost.gost341194
# import pygost.gost3412

from units.cryptography import (
    decode_caesar_cipher, encode_caesar_cipher,
    decode_morse_code, encode_morse_code
)
from utilities import checks


async def setup(bot):
    await bot.add_cog(Cryptography())

class Cryptography(commands.Cog):

    async def cog_check(self, ctx):
        return await checks.not_forbidden().predicate(ctx)

    # TODO: not forbidden global check?

    @commands.hybrid_group(aliases = ["decrpyt"], case_insensitive = True)
    async def decode(self, ctx):
        """Decode encoded messages"""
        await ctx.send_help(ctx.command)

    @decode.group(
        name = "caesar", aliases = ["rot"],
        case_insensitive = True, with_app_command = False
    )
    async def decode_caesar(self, ctx, key: int, *, message: str):
        """Decode caesar cipher"""
        await ctx.embed_reply(decode_caesar_cipher(message, key))

    @decode_caesar.command(name = "brute", with_app_command = False)
    async def decode_caesar_brute(self, ctx, *, message: str):
        '''Brute force decode caesar cipher'''
        # TODO: Paginate if too long
        await ctx.embed_reply('\n'.join(f"{key}: {decode_caesar_cipher(message, key)}" for key in range(26)))

    @decode.group(
        name = "gost", aliases = ["гост"],
        case_insensitive = True, hidden = True
    )
    async def decode_gost(self, ctx):
        """
        Russian Federation/Soviet Union GOST
        Межгосударственный стандарт
        From GOsudarstvennyy STandart
        (ГОсударственный СТандарт)

        This command has been deprecated, as the library it used to use,
        PyGOST, is no longer publicly available on PyPI, the Python Package
        Index
        """
        await ctx.embed_reply(
            "This command has been deprecated, as the library it used to use, "
            "PyGOST, is no longer publicly available on PyPI, the Python "
            "Package Index"
        )
        # await ctx.send_help(ctx.command)

    @decode_gost.command(
        name = "magma", aliases = ["28147-89", "магма"], hidden = True
    )
    async def decode_gost_magma(
        self, ctx, mode: Literal["CBC", "CFB", "CNT", "ECB"], key: str, *,
        data: str
    ):
        """
        GOST 28147-89 block cipher, also known as Магма or Magma

        This command has been deprecated, as the library it used to use,
        PyGOST, is no longer publicly available on PyPI, the Python Package
        Index

        Parameters
        ----------
        mode
            Mode of operation
        key
            Key to use for the cipher
        data
            Data to decode
        """
        await ctx.embed_reply(
            "This command has been deprecated, as the library it used to use, "
            "PyGOST, is no longer publicly available on PyPI, the Python "
            "Package Index"
        )
        # TODO: Add decode magma alias
        # try:
        #     key = key.encode("UTF-8")
        #     data = bytearray.fromhex(data)
        #     if mode == "CBC":
        #         await ctx.embed_reply(
        #             pygost.gost28147.cbc_decrypt(key, data).decode("UTF-8")
        #         )
        #     elif mode == "CFB":
        #         await ctx.embed_reply(
        #             pygost.gost28147.cfb_decrypt(key, data).decode("UTF-8")
        #         )
        #     elif mode == "CNT":
        #         await ctx.embed_reply(
        #             pygost.gost28147.cnt(key, data).decode("UTF-8")
        #         )
        #     elif mode == "ECB":
        #         await ctx.embed_reply(
        #             pygost.gost28147.ecb_decrypt(key, data).decode("UTF-8")
        #         )
        # except ValueError as e:
        #     await ctx.embed_reply(f"{ctx.bot.error_emoji} Error: {e}")

    @decode_gost.command(
        name = "34.12-2015", aliases = ["кузнечик", "kuznyechik"],
        hidden = True, with_app_command = False
    )
    async def decode_gost_34_12_2015(self, ctx, key: str, *, data: str):
        """
        GOST 34.12-2015 128-bit block cipher
        Also known as Кузнечик or Kuznyechik
        key length >= 32, data length >= 16

        This command has been deprecated, as the library it used to use,
        PyGOST, is no longer publicly available on PyPI, the Python Package
        Index
        """
        await ctx.embed_reply(
            "This command has been deprecated, as the library it used to use, "
            "PyGOST, is no longer publicly available on PyPI, the Python "
            "Package Index"
        )
        # TODO: Add decode kuznyechik alias
        # if len(key) < 32:
        #     await ctx.embed_reply(
        #         f"{ctx.bot.error_emoji} Error: key length must be at least 32"
        #     )
        #     return
        # if len(data) < 16:
        #     await ctx.embed_reply(
        #         f"{ctx.bot.error_emoji} Error: data length must be at least 16"
        #     )
        #     return
        # await ctx.embed_reply(
        #     pygost.gost3412.GOST3412Kuznechik(
        #         key.encode("UTF-8")
        #     ).decrypt(
        #         bytearray.fromhex(data)
        #     ).decode("UTF-8")
        # )

    @decode.command(name = "morse")
    async def decode_morse(self, ctx, *, message: str):
        """
        Decode Morse code

        message
            Morse code to decode
        """
        try:
            await ctx.embed_reply(decode_morse_code(message))
        except ValueError as e:
            await ctx.embed_reply(f"{ctx.bot.error_emoji} Error: {e}")

    @decode.command(name = "qr")
    async def decode_qr(
        self, ctx, image: discord.Attachment | None, image_url: str | None
    ):
        """
        Decode QR code
        If both an image and image URL are provided, the image is used

        Parameters
        ----------
        image
            QR code to decode
        image_url
            URL for QR code to decode
        """
        if image:
            image_url = image.url
        elif not image_url:
            await ctx.embed_reply(
                f"{ctx.bot.error_emoji} Image or image URL required",
                ephemeral = True
            )
            return

        await ctx.defer()

        async with ctx.bot.aiohttp_session.get(
            "https://api.qrserver.com/v1/read-qr-code/",
            params = {"fileurl": image_url}
        ) as resp:
            if resp.status == 400:
                await ctx.embed_reply(f"{ctx.bot.error_emoji} Error")
                return

            data = await resp.json()

        if data[0]["symbol"][0]["error"]:
            await ctx.embed_reply(
                f"{ctx.bot.error_emoji} Error: {data[0]['symbol'][0]['error']}"
            )
            return

        decoded = data[0]["symbol"][0]["data"].replace("QR-Code:", "")

        # TODO: Use textwrap
        if len(decoded) > ctx.bot.EMBED_DESCRIPTION_CHARACTER_LIMIT:
            await ctx.embed_reply(
                description = decoded[:ctx.bot.EDCL - 3] + "...",
                # EDCL: Embed Description Character Limit
                footer_text = "Decoded message exceeded character limit"
            )
            return

        await ctx.embed_reply(decoded)

    @decode.command(name = "reverse", with_app_command = False)
    async def decode_reverse(self, ctx, *, message: str):
        """Reverse text"""
        await ctx.embed_reply(message[::-1])

    @commands.hybrid_group(aliases = ["encrypt"], case_insensitive = True)
    async def encode(self, ctx):
        """Encode messages"""
        await ctx.send_help(ctx.command)

    @encode.command(
        name = "adler32", aliases = ["adler-32"], with_app_command = False
    )
    async def encode_adler32(self, ctx, *, message: str):
        """Compute Adler-32 checksum"""
        await ctx.embed_reply(zlib.adler32(message.encode("UTF-8")))

    @encode.command(name = "blake2b", with_app_command = False)
    async def encode_blake2b(self, ctx, *, message: str):
        """64-byte digest BLAKE2b"""
        digest = crypto_hashes.Hash(
            crypto_hashes.BLAKE2b(64), backend = openssl_backend
        )
        digest.update(message.encode("UTF-8"))
        await ctx.embed_reply(digest.finalize())

    @encode.command(name = "blake2s", with_app_command = False)
    async def encode_blake2s(self, ctx, *, message: str):
        """32-byte digest BLAKE2s"""
        digest = crypto_hashes.Hash(
            crypto_hashes.BLAKE2s(32), backend = openssl_backend
        )
        digest.update(message.encode("UTF-8"))
        await ctx.embed_reply(digest.finalize())

    @encode.command(
        name = "caesar", aliases = ["rot"], with_app_command = False
    )
    async def encode_caesar(self, ctx, key: int, *, message: str):
        """Encode a message using a caesar cipher"""
        await ctx.embed_reply(encode_caesar_cipher(message, key))

    @encode.command(
        name = "crc32", aliases = ["crc-32"], with_app_command = False
    )
    async def encode_crc32(self, ctx, *, message: str):
        """Compute CRC32 checksum"""
        await ctx.embed_reply(zlib.crc32(message.encode("UTF-8")))

    @encode.group(
        name = "gost", aliases = ["гост"],
        case_insensitive = True, hidden = True
    )
    async def encode_gost(self, ctx):
        """
        Russian Federation/Soviet Union GOST
        Межгосударственный стандарт
        From GOsudarstvennyy STandart
        (ГОсударственный СТандарт)

        This command has been deprecated, as the library it used to use,
        PyGOST, is no longer publicly available on PyPI, the Python Package
        Index
        """
        await ctx.embed_reply(
            "This command has been deprecated, as the library it used to use, "
            "PyGOST, is no longer publicly available on PyPI, the Python "
            "Package Index"
        )
        # await ctx.send_help(ctx.command)

    @encode_gost.command(
        name = "magma", aliases = ["28147-89", "магма"], hidden = True
    )
    async def encode_gost_magma(
        self, ctx, mode: Literal["CBC", "CFB", "CNT", "ECB", "MAC"], key: str,
        *, data: str
    ):
        """
        GOST 28147-89 block cipher, also known as Магма or Magma

        This command has been deprecated, as the library it used to use,
        PyGOST, is no longer publicly available on PyPI, the Python Package
        Index

        Parameters
        ----------
        mode
            Mode of operation
        key
            Key to use for the cipher; Length must be 32 (256-bit)
        data
            Data to encode; For ECB mode, block size must be 8 (64-bit),
            meaning length must be a multiple of 8
        """
        await ctx.embed_reply(
            "This command has been deprecated, as the library it used to use, "
            "PyGOST, is no longer publicly available on PyPI, the Python "
            "Package Index"
        )
        # TODO: Add encode magma alias
        # try:
        #     key = key.encode("UTF-8")
        #     data = data.encode("UTF-8")
        #     if mode == "CBC":
        #         await ctx.embed_reply(
        #             pygost.gost28147.cbc_encrypt(key, data).hex()
        #         )
        #     elif mode == "CFB":
        #         await ctx.embed_reply(
        #             pygost.gost28147.cfb_encrypt(key, data).hex()
        #         )
        #     elif mode == "CNT":
        #         await ctx.embed_reply(
        #             pygost.gost28147.cnt(key, data).hex()
        #         )
        #     elif mode == "ECB":
        #         await ctx.embed_reply(
        #             pygost.gost28147.ecb_encrypt(key, data).hex()
        #         )
        #     elif mode == "MAC":
        #         mac = pygost.gost28147_mac.MAC(key)
        #         mac.update(data)
        #         await ctx.embed_reply(mac.hexdigest())
        # except ValueError as e:
        #     await ctx.embed_reply(f"{ctx.bot.error_emoji} Error: {e}")

    @encode_gost.command(
        name = "streebog", aliases = ["34.11-2012", "стрибог"], hidden = True
    )
    async def encode_gost_streebog(
        self, ctx, digest_size: Literal[256, 512], *, data: str
    ):
        """
        GOST 34.11-2012 hash function, also known as Стрибог or Streebog
        256-bit or 512-bit, also known as Streebog-256 or Streebog-512

        This command has been deprecated, as the library it used to use,
        PyGOST, is no longer publicly available on PyPI, the Python Package
        Index

        Parameters
        ----------
        digest_size
            Digest/Block size: 256-bit or 512-bit
        data
            Data to hash
        """
        await ctx.embed_reply(
            "This command has been deprecated, as the library it used to use, "
            "PyGOST, is no longer publicly available on PyPI, the Python "
            "Package Index"
        )
        # TODO: Add encode streebog-256 and encode streebog-512 
        # data = data.encode("UTF-8")
        # if digest_size == 256:
        #     await ctx.embed_reply(
        #         pygost.gost34112012.GOST34112012(
        #             data, digest_size = 32
        #         ).hexdigest()
        #     )
        # elif digest_size == 512:
        #     await ctx.embed_reply(
        #         pygost.gost34112012.GOST34112012(
        #             data, digest_size = 64
        #         ).hexdigest()
        #     )

    @encode_gost.command(
        name = "34.11-94", hidden = True, with_app_command = False
    )
    async def encode_gost_34_11_94(self, ctx, *, data: str):
        """
        GOST 34.11-94 hash function

        This command has been deprecated, as the library it used to use,
        PyGOST, is no longer publicly available on PyPI, the Python Package
        Index
        """
        await ctx.embed_reply(
            "This command has been deprecated, as the library it used to use, "
            "PyGOST, is no longer publicly available on PyPI, the Python "
            "Package Index"
        )
        # await ctx.embed_reply(
        #     pygost.gost341194.GOST341194(
        #         data.encode("UTF-8")
        #     ).hexdigest()
        # )

    @encode_gost.command(
        name = "34.12-2015", aliases = ["кузнечик", "kuznyechik"],
        hidden = True, with_app_command = False
    )
    async def encode_gost_34_12_2015(self, ctx, key: str, *, data: str):
        """
        GOST 34.12-2015 128-bit block cipher
        Also known as Кузнечик or Kuznyechik
        key length >= 32, data length >= 16

        This command has been deprecated, as the library it used to use,
        PyGOST, is no longer publicly available on PyPI, the Python Package
        Index
        """
        await ctx.embed_reply(
            "This command has been deprecated, as the library it used to use, "
            "PyGOST, is no longer publicly available on PyPI, the Python "
            "Package Index"
        )
        # TODO: Add encode kuznyechik alias
        # if len(key) < 32:
        #     await ctx.embed_reply(
        #         f"{ctx.bot.error_emoji} Error: key length must be at least 32"
        #     )
        #     return
        # if len(data) < 16:
        #     await ctx.embed_reply(
        #         f"{ctx.bot.error_emoji} Error: data length must be at least 16"
        #     )
        #     return
        # await ctx.embed_reply(
        #     pygost.gost3412.GOST3412Kuznechik(
        #         key.encode("UTF-8")
        #     ).encrypt(
        #         data.encode("UTF-8")
        #     ).hex()
        # )

    @encode.command(name = "md4", with_app_command = False)
    async def encode_md4(self, ctx, *, message: str):
        """Generate MD4 hash"""
        md4_hash = hashlib.new("MD4")
        md4_hash.update(message.encode("UTF-8"))
        await ctx.embed_reply(md4_hash.hexdigest())

    @encode.command(name = "md5", with_app_command = False)
    async def encode_md5(self, ctx, *, message: str):
        """Generate MD5 hash"""
        await ctx.embed_reply(hashlib.md5(message.encode("UTF-8")).hexdigest())

    @encode.command(name = "morse")
    async def encode_morse(self, ctx, *, message: str):
        """
        Encode a message in Morse code

        Parameters
        ----------
        message
            Message to encode
        """
        try:
            await ctx.embed_reply(encode_morse_code(message))
        except ValueError as e:
            await ctx.embed_reply(f"{ctx.bot.error_emoji} Error: {e}")

    @encode.command(name = "qr")
    async def encode_qr(self, ctx, *, message: str):
        """
        Encode a message in a QR code
        
        Parameters
        ----------
        message
            Message to encode
        """
        message = message.replace(' ', '+')
        url = "https://api.qrserver.com/v1/create-qr-code/?data=" + message
        await ctx.embed_reply(image_url = url)

    @encode.command(name = "reverse", with_app_command = False)
    async def encode_reverse(self, ctx, *, message: str):
        """Reverse text"""
        await ctx.embed_reply(message[::-1])

    @encode.command(
        name = "ripemd160", aliases = ["ripemd-160"], with_app_command = False
    )
    async def encode_ripemd160(self, ctx, *, message: str):
        """Generate RIPEMD-160 hash"""
        h = hashlib.new("RIPEMD160")
        h.update(message.encode("UTF-8"))
        await ctx.embed_reply(h.hexdigest())

    @encode.command(
        name = "sha1", aliases = ["sha-1"], with_app_command = False
    )
    async def encode_sha1(self, ctx, *, message: str):
        """Generate SHA-1 hash"""
        await ctx.embed_reply(
            hashlib.sha1(  # nosec hashlib
                message.encode("UTF-8")
            ).hexdigest()
        )

    @encode.command(
        name = "sha224", aliases = ["sha-224"], with_app_command = False
    )
    async def encode_sha224(self, ctx, *, message: str):
        """Generate SHA-224 hash"""
        await ctx.embed_reply(
            hashlib.sha224(
                message.encode("UTF-8")
            ).hexdigest()
        )

    @encode.command(
        name = "sha256", aliases = ["sha-256"], with_app_command = False
    )
    async def encode_sha256(self, ctx, *, message: str):
        """Generate SHA-256 hash"""
        await ctx.embed_reply(
            hashlib.sha256(
                message.encode("UTF-8")
            ).hexdigest()
        )

    @encode.command(
        name = "sha384", aliases = ["sha-384"], with_app_command = False
    )
    async def encode_sha384(self, ctx, *, message: str):
        """Generate SHA-384 hash"""
        await ctx.embed_reply(
            hashlib.sha384(
                message.encode("UTF-8")
            ).hexdigest()
        )

    @encode.command(
        name = "sha512", aliases = ["sha-512"], with_app_command = False
    )
    async def encode_sha512(self, ctx, *, message: str):
        """Generate SHA-512 hash"""
        await ctx.embed_reply(
            hashlib.sha512(
                message.encode("UTF-8")
            ).hexdigest()
        )

    @encode.command(name = "whirlpool", with_app_command = False)
    async def encode_whirlpool(self, ctx, *, message: str):
        """Generate WHIRLPOOL hash"""
        h = hashlib.new("WHIRLPOOL")
        h.update(message.encode("UTF-8"))
        await ctx.embed_reply(h.hexdigest())

