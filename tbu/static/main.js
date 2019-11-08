FilePond.registerPlugin(FilePondPluginFileValidateType);
FilePond.create(document.querySelector('input'), {
    acceptedFileTypes: ['.java'],
    fileValidateTypeDetectType: (source, type) => new Promise((resolve, reject) => {
        if (source.name.endsWith('.java') || source.name.endsWith('.JAVA')) resolve('.java');
        else resolve(type);
    })
});
