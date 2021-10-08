using CommandLine;
using ICSharpCode.SharpZipLib.GZip;
using Kanvas;
using Kontract.Models.Image;
using System.Drawing;

Parser.Default.ParseArguments<Options>(args)
       .WithParsed<Options>(o =>
       {
           if (o.Extract)
           {
               Extract(o.Input, o.Image);
           }
           else if (o.Import)
           {
               Import(o.Input, o.Image, o.Mtxt);
           }
       });


static void Extract(string mtxtPath, string imagePath)
{
    using (var fs = File.OpenRead(mtxtPath))
    {
        BinaryReader reader = new BinaryReader(fs);
        var magic = reader.ReadChars(4);
        if (!magic.SequenceEqual("MTXT"))
        {
            throw new Exception("Invalid file format");
        }

        var version = reader.ReadBytes(4);

        using (var decompressedStream = new MemoryStream())
        {
            GZip.Decompress(fs, decompressedStream, false);

            var dataReader = new BinaryReader(decompressedStream);
            decompressedStream.Position = 8;
            int width = dataReader.ReadInt32();
            int height = dataReader.ReadInt32();

            decompressedStream.Position = 0x278;
            var rawDxt5Data = dataReader.ReadBytes(width * height);

            var definition = new EncodingDefinition();
            definition.AddColorEncoding(0, ImageFormats.Dxt5());
            ImageInfo imageInfo = new ImageInfo(rawDxt5Data, 0, new System.Drawing.Size(width, height));
            imageInfo.RemapPixels.With(contex => new Kanvas.Swizzle.NxSwizzle(contex));
            var kimg = new KanvasImage(definition, imageInfo);

            kimg.GetImage().Save(imagePath);
        }
    }
}

static void Import(string mtxtPath, string imagePath, string outputPath)
{
    using (var fs = File.OpenRead(mtxtPath))
    {
        BinaryReader reader = new BinaryReader(fs);
        var magic = reader.ReadChars(4);
        if (!magic.SequenceEqual("MTXT"))
        {
            throw new Exception("Invalid file format");
        }

        var version = reader.ReadBytes(4);

        using (var decompressedStream = new MemoryStream())
        {
            GZip.Decompress(fs, decompressedStream, false);

            var dataReader = new BinaryReader(decompressedStream);
            decompressedStream.Position = 8;
            int width = dataReader.ReadInt32();
            int height = dataReader.ReadInt32();

            decompressedStream.Position = 0x278;
            var rawDxt5Data = dataReader.ReadBytes(width * height);

            var definition = new EncodingDefinition();
            definition.AddColorEncoding(0, ImageFormats.Dxt5());
            ImageInfo imageInfo = new ImageInfo(rawDxt5Data, 0, new System.Drawing.Size(width, height));
            imageInfo.RemapPixels.With(contex => new Kanvas.Swizzle.NxSwizzle(contex));
            var kimg = new KanvasImage(definition, imageInfo);

            kimg.SetImage((Bitmap)Image.FromFile(imagePath));
            rawDxt5Data = imageInfo.ImageData;
            decompressedStream.Position = 0x278;
            decompressedStream.Write(rawDxt5Data, 0, rawDxt5Data.Length);

            using (var outfs = File.Create(outputPath))
            {
                fs.Position = 0;
                outfs.Write(reader.ReadBytes(8), 0, 8);
                decompressedStream.Position = 0;
                GZip.Compress(decompressedStream, outfs, false);
            }
        }
    }
}

public class Options
{
    [Option('x', "extract", HelpText = "Extract image from MTXT file")]
    public bool Extract { get; set; }

    [Option('i', "import", HelpText = "Import image into MTXT file")]
    public bool Import { get; set; }

    [Option('t', "mtxt", HelpText = "Path to MTXT file")]
    public string Mtxt { get; set; }

    [Option('g', "image", HelpText = "Path to image file")]
    public string Image { get; set; }

    [Value(0, Required = true, HelpText = "Path to input MTXT file")]
    public string Input { get; set; }
}