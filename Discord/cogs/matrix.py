
from discord.ext import commands

import ast
import numpy
import scipy

from utilities import checks


async def setup(bot):
    await bot.add_cog(Matrix())

class Matrix(commands.Cog):

    # TODO: move to converters file
    class Matrix(commands.Converter):
        async def convert(self, ctx, argument):
            try:
                return ast.literal_eval(argument)
            except SyntaxError:
                raise commands.BadArgument("Syntax Error")
            # TODO: check matrix

    async def cog_check(self, ctx):
        return await checks.not_forbidden().predicate(ctx)

    @commands.group(
        aliases = ["matrices"],
        case_insensitive = True, invoke_without_command = True
    )
    async def matrix(self, ctx):
        """
        Matrix operations
        Input matrices as a list of lists (array of arrays)
        e.g.: [[1,2],[3,4]]
        """
        await ctx.send_help(ctx.command)

    @matrix.command(aliases = ["addition", "plus", '+'])
    async def add(self, ctx, matrix_a: Matrix, matrix_b: Matrix):
        """Add two matrices"""
        # TODO: unlimited number?
        await ctx.embed_reply(
            str(numpy.matrix(matrix_a) + numpy.matrix(matrix_b))
        )

    @matrix.group(
        aliases = ["cosine"],
        case_insensitive = True, invoke_without_command = True
    )
    async def cos(self, ctx, *, matrix: Matrix):
        """Cosine of a matrix"""
        await ctx.embed_reply(str(scipy.linalg.cosm(matrix)))

    @cos.command(name = "hyperbolic", aliases = ['h'])
    async def cos_hyperbolic(self, ctx, *, matrix: Matrix):
        """Hyperbolic cosine of a matrix"""
        await ctx.embed_reply(str(scipy.linalg.coshm(matrix)))

    @matrix.command()
    async def determinant(self, ctx, *, matrix: Matrix):
        """Determinant of a matrix"""
        await ctx.embed_reply(scipy.linalg.det(matrix))

    @matrix.command(aliases = ["division", '/'])
    async def divide(self, ctx, matrix_a: Matrix, matrix_b: Matrix):
        """Divide two matrices"""
        await ctx.embed_reply(
            str(numpy.matrix(matrix_a) / numpy.matrix(matrix_b))
        )

    @matrix.command(naliases = ["exponential"])
    async def exp(self, ctx, matrix: Matrix):
        """Compute the matrix exponential using Pade approximation"""
        await ctx.embed_reply(str(scipy.linalg.expm(matrix)))

    @matrix.command()
    async def inverse(self, ctx, *, matrix: Matrix):
        """Inverse of a matrix"""
        await ctx.embed_reply(str(numpy.matrix(matrix).I))

    @matrix.command(aliases = ["logarithm"])
    async def log(self, ctx, *, matrix: Matrix):
        """Compute matrix logarithm"""
        await ctx.embed_reply(str(scipy.linalg.logm(matrix)))

    @matrix.command()
    async def lu(self, ctx, *, matrix: Matrix):
        """LU decomposition of a matrix"""
        p, l, u = scipy.linalg.lu(matrix)
        await ctx.embed_reply(fields = (("P", p), ("L", l), ("U", u)))

    @matrix.group(
        aliases = ["times", '*'],
        case_insensitive = True, invoke_without_command = True
    )
    async def multiply(self, ctx, matrix_a: Matrix, matrix_b: Matrix):
        """Multiply two matrices"""
        await ctx.embed_reply(
            str(numpy.matrix(matrix_a) * numpy.matrix(matrix_b))
        )

    @multiply.command(name = "scalar")
    async def multiply_scalar(self, ctx, matrix: Matrix, scalar: float):
        """Multiply a matrix by a scalar"""
        await ctx.embed_reply(str(numpy.matrix(matrix) * scalar))

    @matrix.command(aliases = ['^', "**"])
    async def power(self, ctx, matrix: Matrix, power: int):
        """Raise a matrix to a power"""
        try:
            await ctx.embed_reply(str(numpy.matrix(matrix) ** power))
        except ValueError as e:  # not square matrix
            await ctx.embed_reply(f"{ctx.bot.error_emoji} Error: {e}")

    @matrix.command()
    async def rank(self, ctx, matrix: Matrix):
        """Rank of a matrix"""
        await ctx.embed_reply(numpy.linalg.matrix_rank(matrix))

    @matrix.command()
    async def sign(self, ctx, matrix: Matrix):
        """Matrix sign function"""
        await ctx.embed_reply(str(scipy.linalg.signm(matrix)))

    @matrix.group(
        aliases = ["sine"],
        case_insensitive = True, invoke_without_command = True
    )
    async def sin(self, ctx, *, matrix: Matrix):
        """Sine of a matrix"""
        await ctx.embed_reply(str(scipy.linalg.sinm(matrix)))

    @sin.command(name = "hyperbolic", aliases = ['h'])
    async def sin_hyperbolic(self, ctx, *, matrix: Matrix):
        """Hyperbolic sine of a matrix"""
        await ctx.embed_reply(str(scipy.linalg.sinhm(matrix)))

    @matrix.command(aliases = ["squareroot", "square_root", '√'])
    async def sqrt(self, ctx, *, matrix: Matrix):
        """Square root of a matrix"""
        await ctx.embed_reply(str(scipy.linalg.sqrtm(matrix)))

    @matrix.command(aliases = ["subtraction", "minus", '-'])
    async def subtract(self, ctx, matrix_a: Matrix, matrix_b: Matrix):
        """Subtract two matrices"""
        await ctx.embed_reply(
            str(numpy.matrix(matrix_a) - numpy.matrix(matrix_b))
        )

    @matrix.group(
        aliases = ["tangent"],
        case_insensitive = True, invoke_without_command = True
    )
    async def tan(self, ctx, *, matrix: Matrix):
        """Tangent of a matrix"""
        await ctx.embed_reply(str(scipy.linalg.tanm(matrix)))

    @tan.command(name = "hyperbolic", aliases = ['h'])
    async def tan_hyperbolic(self, ctx, *, matrix: Matrix):
        """Hyperbolic tangent of a matrix"""
        await ctx.embed_reply(str(scipy.linalg.tanhm(matrix)))

    @matrix.group(
        aliases = ["transposition"],
        case_insensitive = True, invoke_without_command = True
    )
    async def transpose(self, ctx, *, matrix: Matrix):
        """Transpose of a matrix"""
        await ctx.embed_reply(str(numpy.matrix(matrix).T))

    @transpose.command(name = "conjugate")
    async def transpose_conjugate(self, ctx, *, matrix: Matrix):
        """Conjugate trasponse of a matrix"""
        await ctx.embed_reply(str(numpy.matrix(matrix).H))

